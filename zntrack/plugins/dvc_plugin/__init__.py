import dataclasses
import json
import pathlib
import typing as t

import pandas as pd
import yaml
import znflow
import znjson

from zntrack import converter
from zntrack.config import (
    PARAMS_FILE_PATH,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
    ZNTRACK_FILE_PATH,
    ZNTRACK_LAZY_VALUE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.converter import (
    CombinedConnectionsConverter,
    ConnectionConverter,
    NodeConverter,
    node_to_output_paths,
)
from zntrack.exceptions import NodeNotAvailableError
from zntrack.plugins import ZnTrackPlugin, base_getter
from zntrack.utils.misc import TempPathLoader, get_attr_always_list
from zntrack.utils.node_wd import NWDReplaceHandler

if t.TYPE_CHECKING:
    from zntrack import Node


def _outs_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _metrics_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _plots_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".csv").write_text(getattr(self, name).to_csv())


def _paths_getter(self: "Node", name: str):
    nwd_handler = NWDReplaceHandler()

    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        return nwd_handler(self.__dict__[name], nwd=self.nwd)
    try:
        with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
            content = json.load(f)[self.name][name]
            content = znjson.loads(json.dumps(content))
            content = nwd_handler(content, nwd=self.nwd)

            if self.state.tmp_path is not None:
                loader = TempPathLoader()
                return loader(content, instance=self)

            return content
    except FileNotFoundError:
        raise NodeNotAvailableError(f"Node '{self.name}' is not available")


def _deps_getter(self: "Node", name: str):
    with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        # TODO: Ensure deps are loaded from the correct revision
        content = znjson.loads(
            json.dumps(content),
            cls=znjson.ZnDecoder.from_converters(
                [NodeConverter, ConnectionConverter, CombinedConnectionsConverter],
                add_default=True,
            ),
        )

        # Resolve any connections in content
        if isinstance(content, list):
            content = [
                (
                    c.result
                    if isinstance(c, (znflow.Connection, znflow.CombinedConnections))
                    else c
                )
                for c in content
            ]
        elif isinstance(content, (znflow.Connection, znflow.CombinedConnections)):
            content = content.result

        self.__dict__[name] = content


def _params_getter(self: "Node", name: str):
    with self.state.fs.open(PARAMS_FILE_PATH) as f:
        self.__dict__[name] = yaml.safe_load(f)[self.name][name]


def _outs_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".json")) as f:
        self.__dict__[name] = json.load(f)


def _plots_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".csv")) as f:
        self.__dict__[name] = pd.read_csv(f)


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
        elif option in {
            ZnTrackOptionEnum.PARAMS_PATH,
            ZnTrackOptionEnum.DEPS_PATH,
            ZnTrackOptionEnum.OUTS_PATH,
            ZnTrackOptionEnum.PLOTS_PATH,
            ZnTrackOptionEnum.METRICS_PATH,
        }:
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
        if len(data) > 0:
            return data
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_dvc_yaml(self) -> dict | object:
        node_dict = NodeConverter().encode(self.node)

        stages = {
            "cmd": f"zntrack run {node_dict['module']}.{node_dict['cls']} --name {node_dict['name']}",
            "metrics": [
                {(self.node.nwd / "node-meta.json").as_posix(): {"cache": False}}
            ],
        }
        plots = {}

        nwd_handler = NWDReplaceHandler()

        for field in dataclasses.fields(self.node):
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
                stages.setdefault(ZnTrackOptionEnum.PARAMS.value, []).append(
                    self.node.name
                )
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS_PATH:
                content = nwd_handler(
                    get_attr_always_list(self.node, field.name), nwd=self.node.nwd
                )
                content = [{pathlib.Path(x).as_posix(): None} for x in content]
                stages.setdefault(ZnTrackOptionEnum.PARAMS.value, []).extend(content)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.OUTS_PATH:
                content = nwd_handler(
                    get_attr_always_list(self.node, field.name), nwd=self.node.nwd
                )
                content = [pathlib.Path(x).as_posix() for x in content]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.OUTS.value, []).extend(content)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS_PATH:
                content = nwd_handler(
                    get_attr_always_list(self.node, field.name), nwd=self.node.nwd
                )
                content = [pathlib.Path(x).as_posix() for x in content]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.OUTS.value, []).extend(content)
                # plots[self.node.name] = None
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS_PATH:
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
                # cache
                # plots[self.node.name] = None
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
                content = [(self.node.nwd / field.name).with_suffix(".json").as_posix()]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(ZnTrackOptionEnum.METRICS.value, []).extend(content)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.DEPS:
                content = get_attr_always_list(self.node, field.name)
                paths = []
                for con in content:
                    if isinstance(con, (znflow.Connection)):
                        paths.extend(node_to_output_paths(con.instance))
                    elif isinstance(con, (znflow.CombinedConnections)):
                        for _con in con.connections:
                            paths.extend(node_to_output_paths(_con.instance))
                stages.setdefault(ZnTrackOptionEnum.DEPS.value, []).extend(paths)
            elif field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.DEPS_PATH:
                content = [
                    pathlib.Path(c).as_posix()
                    for c in get_attr_always_list(self.node, field.name)
                ]
                stages.setdefault(ZnTrackOptionEnum.DEPS.value, []).extend(content)

        def sort_key(item):
            """Custom sorting key function to handle both string and dictionary types."""
            if isinstance(item, str):
                return item
            elif isinstance(item, dict):
                # For dictionaries, sort by their first (and only) key's string representation
                return list(item.keys())[0]

        for key in stages:
            if key == "cmd":
                continue
            stages[key] = sorted(stages[key], key=sort_key)

        for key in plots:
            plots[key] = sorted(plots[key], key=sort_key)

        return {"stages": stages, "plots": plots}

    def convert_to_zntrack_json(self) -> dict | object:
        data = {
            "nwd": self.node.nwd,
        }
        for field in dataclasses.fields(self.node):
            if field.metadata.get(ZNTRACK_OPTION) in [
                ZnTrackOptionEnum.PARAMS,
                ZnTrackOptionEnum.OUTS,
                ZnTrackOptionEnum.PLOTS,
                ZnTrackOptionEnum.METRICS,
            ]:
                continue
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
                ],
                add_default=False,
            ),
        )
        return json.loads(data)
