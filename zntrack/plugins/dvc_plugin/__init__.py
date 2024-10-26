import contextlib
import copy
import dataclasses
import json
import pathlib
import typing as t

import pandas as pd
import yaml
import znflow
import znflow.handler
import znflow.utils
import znjson

from zntrack import converter
from zntrack.config import (
    NOT_AVAILABLE,
    PARAMS_FILE_PATH,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
    ZNTRACK_FILE_PATH,
    ZNTRACK_LAZY_VALUE,
    ZNTRACK_OPTION,
    ZNTRACK_OPTION_PLOTS_CONFIG,
    ZnTrackOptionEnum,
)

# if t.TYPE_CHECKING:
from zntrack.node import Node
from zntrack.plugins import ZnTrackPlugin, base_getter
from zntrack.utils import module_handler
from zntrack.utils.misc import (
    RunDVCImportPathHandler,
    TempPathLoader,
    get_attr_always_list,
    sort_and_deduplicate,
)
from zntrack.utils.node_wd import NWDReplaceHandler, nwd


def _outs_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _metrics_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _plots_save_func(self: "Node", name: str):
    content = getattr(self, name)
    if not isinstance(content, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(content)}")
    content.to_csv((self.nwd / name).with_suffix(".csv"))


def _paths_getter(self: "Node", name: str):
    # TODO: if self._external_: try looking into
    # external/self.uuid/...
    # this works for everything except node-meta.json because that
    # defines the uuid
    nwd_handler = NWDReplaceHandler()

    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        return nwd_handler(self.__dict__[name], nwd=self.nwd)
    try:
        with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
            content = json.load(f)[self.name][name]
            content = znjson.loads(json.dumps(content))

            if self.state.tmp_path is not None:
                loader = TempPathLoader()
                loader(content, instance=self)

            content = nwd_handler(content, nwd=self.nwd)

            return content
    except FileNotFoundError:
        return NOT_AVAILABLE


def _deps_getter(self: "Node", name: str):
    with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        # TODO: Ensure deps are loaded from the correct revision
        content = znjson.loads(
            json.dumps(content),
            cls=znjson.ZnDecoder.from_converters(
                [
                    converter.NodeConverter,
                    converter.ConnectionConverter,
                    converter.CombinedConnectionsConverter,
                    converter.DVCImportPathConverter,
                    converter.DataclassConverter,
                ],
                add_default=True,
            ),
        )
        if isinstance(content, converter.DataclassContainer):
            content = content.get_with_params(self.name, name)
        if isinstance(content, list):
            new_content = []
            idx = 0
            for val in content:
                if isinstance(val, converter.DataclassContainer):
                    new_content.append(val.get_with_params(self.name, name, idx))
                    idx += 1  # index only runs over dataclasses
                else:
                    new_content.append(val)
            content = new_content

        content = znflow.handler.UpdateConnectors()(content)

        self.__dict__[name] = content


def _params_getter(self: "Node", name: str):
    with self.state.fs.open(PARAMS_FILE_PATH) as f:
        self.__dict__[name] = yaml.safe_load(f)[self.name][name]


def _outs_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".json")) as f:
        self.__dict__[name] = json.load(f, cls=znjson.ZnDecoder)


def _plots_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".csv")) as f:
        self.__dict__[name] = pd.read_csv(f, index_col=0)


@dataclasses.dataclass
class DVCPlugin(ZnTrackPlugin):
    def getter(self, field: dataclasses.Field) -> t.Any:
        option = field.metadata.get(ZNTRACK_OPTION)

        if option == ZnTrackOptionEnum.DEPS:
            return base_getter(self.node, field.name, _deps_getter)
        elif option == ZnTrackOptionEnum.PARAMS:
            return base_getter(self.node, field.name, _params_getter)
        elif option == ZnTrackOptionEnum.PLOTS:
            return base_getter(self.node, field.name, _plots_getter)
        elif option in {
            ZnTrackOptionEnum.OUTS,
            ZnTrackOptionEnum.METRICS,
        }:
            return base_getter(self.node, field.name, _outs_getter)
        elif option == ZnTrackOptionEnum.DEPS_PATH:
            return _paths_getter(self.node, field.name)
        elif option in {
            ZnTrackOptionEnum.PARAMS_PATH,
            ZnTrackOptionEnum.OUTS_PATH,
            ZnTrackOptionEnum.PLOTS_PATH,
            ZnTrackOptionEnum.METRICS_PATH,
        }:
            # TODO: do not use nwd_handler for deps_path and params_path
            return _paths_getter(self.node, field.name)
        return PLUGIN_EMPTY_RETRUN_VALUE

    def save(self, field: dataclasses.Field) -> None:
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.OUTS:
            _outs_save_func(self.node, field.name)
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS:
            _plots_save_func(self.node, field.name)
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
            _metrics_save_func(self.node, field.name)

    def convert_to_params_yaml(self) -> dict | object:
        data = {}
        for field in dataclasses.fields(self.node):
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
                data[field.name] = getattr(self.node, field.name)
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.DEPS:
                if getattr(self.node, field.name) is None:
                    continue
                content = getattr(self.node, field.name)
                if isinstance(content, (list, tuple, dict)):
                    new_content = []
                    for val in (
                        content
                        if isinstance(content, (list, tuple))
                        else content.values()
                    ):
                        if dataclasses.is_dataclass(val) and not isinstance(
                            val, (Node, znflow.Connection, znflow.CombinedConnections)
                        ):
                            # We save the values of the passed dataclasses
                            #  to the params.yaml file to be later used
                            #  by the DataclassContainer to recreate the
                            #  instance with the correct parameters.
                            dc_params = dataclasses.asdict(val)
                            dc_params["_cls"] = (
                                f"{module_handler(val)}.{val.__class__.__name__}"
                            )
                            new_content.append(dc_params)
                        elif isinstance(
                            val, (znflow.Connection, znflow.CombinedConnections)
                        ):
                            pass
                        else:
                            raise ValueError(
                                f"Found unsupported type '{type(val)}' ({val}) for DEPS field '{field.name}' in list"
                            )
                    if len(new_content) > 0:
                        data[field.name] = new_content
                elif dataclasses.is_dataclass(content) and not isinstance(
                    content, (Node, znflow.Connection, znflow.CombinedConnections)
                ):
                    dc_params = dataclasses.asdict(content)
                    dc_params["_cls"] = (
                        f"{module_handler(content)}.{content.__class__.__name__}"
                    )
                    data[field.name] = dc_params
                elif isinstance(content, (znflow.Connection, znflow.CombinedConnections)):
                    pass
                else:
                    raise ValueError(
                        f"Found unsupported type '{type(content)}' ({content}) for DEPS field '{field.name}'"
                    )

        if len(data) > 0:
            return data
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_dvc_yaml(self) -> dict | object:
        node_dict = converter.NodeConverter().encode(self.node)

        cmd = f"zntrack run {node_dict['module']}.{node_dict['cls']} --name {node_dict['name']}"
        if hasattr(self.node, "_method"):
            cmd += f" --method {self.node._method}"
        stages = {
            "cmd": cmd,
            "metrics": [
                {(self.node.nwd / "node-meta.json").as_posix(): {"cache": False}}
            ],
        }
        if self.node.always_changed:
            stages["always_changed"] = True
        plots = []

        nwd_handler = NWDReplaceHandler()

        for field in dataclasses.fields(self.node):
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
                stages.setdefault(ZnTrackOptionEnum.PARAMS.value, []).append(
                    self.node.name
                )
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS_PATH:
                if getattr(self.node, field.name) is None:
                    continue
                content = nwd_handler(
                    get_attr_always_list(self.node, field.name), nwd=self.node.nwd
                )
                content = [{pathlib.Path(x).as_posix(): None} for x in content]
                stages.setdefault(ZnTrackOptionEnum.PARAMS.value, []).extend(content)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.OUTS_PATH:
                if getattr(self.node, field.name) is None:
                    continue
                if getattr(self.node, field.name) == nwd:
                    raise ValueError(
                        "Can not use 'zntrack.nwd' direclty as an output path. Please use 'zntrack.nwd / <path/file>' instead."
                    )
                content = nwd_handler(
                    get_attr_always_list(self.node, field.name), nwd=self.node.nwd
                )
                content = [pathlib.Path(x).as_posix() for x in content]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.OUTS.value, []).extend(content)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS_PATH:
                if getattr(self.node, field.name) is None:
                    continue
                content = nwd_handler(
                    get_attr_always_list(self.node, field.name), nwd=self.node.nwd
                )
                content = [pathlib.Path(x).as_posix() for x in content]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.OUTS.value, []).extend(content)
                # plots[self.node.name] = None
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS_PATH:
                if getattr(self.node, field.name) is None:
                    continue
                content = nwd_handler(
                    get_attr_always_list(self.node, field.name), nwd=self.node.nwd
                )
                content = [pathlib.Path(x).as_posix() for x in content]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.METRICS.value, []).extend(content)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.OUTS:
                content = [(self.node.nwd / field.name).with_suffix(".json").as_posix()]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.OUTS.value, []).extend(content)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS:
                content = [(self.node.nwd / field.name).with_suffix(".csv").as_posix()]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.OUTS.value, []).extend(content)
                if ZNTRACK_OPTION_PLOTS_CONFIG in field.metadata:
                    file_path = (
                        (self.node.nwd / field.name).with_suffix(".csv").as_posix()
                    )
                    plots_config = field.metadata[ZNTRACK_OPTION_PLOTS_CONFIG].copy()
                    if "x" not in plots_config or "y" not in plots_config:
                        raise ValueError(
                            "Both 'x' and 'y' must be specified in the plots_config."
                        )
                    if "x" in plots_config:
                        plots_config["x"] = {file_path: plots_config["x"]}
                    if isinstance(plots_config["y"], list):
                        for idx, y in enumerate(plots_config["y"]):
                            cfg = copy.deepcopy(plots_config)
                            cfg["y"] = {file_path: y}
                            plots.append({f"{self.node.name}_{field.name}_{idx}": cfg})
                    else:
                        if "y" in plots_config:
                            plots_config["y"] = {file_path: plots_config["y"]}
                        plots.append({f"{self.node.name}_{field.name}": plots_config})
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
                content = [(self.node.nwd / field.name).with_suffix(".json").as_posix()]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.METRICS.value, []).extend(content)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.DEPS:
                if getattr(self.node, field.name) is None:
                    continue
                content = get_attr_always_list(self.node, field.name)
                paths = []
                for con in content:
                    if isinstance(con, (znflow.Connection)):
                        if con.item is not None:
                            raise NotImplementedError(
                                "znflow.Connection getitem is not supported yet."
                            )
                        paths.extend(
                            converter.node_to_output_paths(con.instance, con.attribute)
                        )
                    elif isinstance(con, (znflow.CombinedConnections)):
                        for _con in con.connections:
                            if con.item is not None:
                                raise NotImplementedError(
                                    "znflow.Connection getitem is not supported yet."
                                )
                            paths.extend(
                                converter.node_to_output_paths(
                                    _con.instance, _con.attribute
                                )
                            )
                    elif dataclasses.is_dataclass(con) and not isinstance(con, Node):
                        # add node name to params.yaml
                        stages.setdefault(ZnTrackOptionEnum.PARAMS.value, []).append(
                            self.node.name
                        )
                    else:
                        raise ValueError("unsupoorted type")

                if len(paths) > 0:
                    stages.setdefault(ZnTrackOptionEnum.DEPS.value, []).extend(paths)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.DEPS_PATH:
                if getattr(self.node, field.name) is None:
                    continue
                content = [
                    pathlib.Path(c).as_posix()
                    for c in get_attr_always_list(self.node, field.name)
                ]
                RunDVCImportPathHandler()(self.node.__dict__.get(field.name))
                stages.setdefault(ZnTrackOptionEnum.DEPS.value, []).extend(content)

        for key in stages:
            if key in ["cmd", "always_changed"]:
                continue
            stages[key] = sort_and_deduplicate(stages[key])

        return {"stages": stages, "plots": plots}

    def convert_to_zntrack_json(self, graph) -> dict | object:
        data = {
            "nwd": self.node.nwd,
        }
        for field in dataclasses.fields(self.node):
            if field.metadata.get(ZNTRACK_OPTION) in [
                ZnTrackOptionEnum.PARAMS_PATH,
                ZnTrackOptionEnum.DEPS_PATH,
                ZnTrackOptionEnum.OUTS_PATH,
                ZnTrackOptionEnum.PLOTS_PATH,
                ZnTrackOptionEnum.METRICS_PATH,
                ZnTrackOptionEnum.DEPS,
            ]:
                data[field.name] = self.node.__dict__[field.name]

        data = znjson.dumps(
            data,
            indent=4,
            cls=znjson.ZnEncoder.from_converters(
                [
                    converter.ConnectionConverter,
                    converter.NodeConverter,
                    converter.CombinedConnectionsConverter,
                    znjson.converter.PathlibConverter,
                    converter.DVCImportPathConverter,
                    converter.DataclassConverter,
                ],
                add_default=False,
            ),
        )
        return json.loads(data)
