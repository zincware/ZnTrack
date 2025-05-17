import copy
import dataclasses
import json
import logging
import pathlib
import typing as t

import znflow
import znjson

from zntrack import config, converter
from zntrack.config import (
    FIELD_TYPE,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FIELD_SUFFIX,
    ZNTRACK_OPTION_PLOTS_CONFIG,
    FieldTypes,
)

# if t.TYPE_CHECKING:
from zntrack.node import Node
from zntrack.plugins import ZnTrackPlugin
from zntrack.plugins.dvc_plugin.dvc import (
    metrics_path_to_dvc,
    outs_path_to_dvc,
    outs_to_dvc,
    params_path_to_dvc,
    plots_path_to_dvc,
    metrics_to_dvc,
    deps_path_to_dvc,
    deps_to_dvc,
)
from zntrack.plugins.dvc_plugin.params import deps_to_params
from zntrack.utils.misc import (
    RunDVCImportPathHandler,
    get_attr_always_list,
    sort_and_deduplicate,
)
from zntrack.utils.node_wd import NWDReplaceHandler, nwd

log = logging.getLogger(__name__)


@dataclasses.dataclass
class DVCPlugin(ZnTrackPlugin):
    def getter(self, field: dataclasses.Field) -> t.Any:
        getter = field.metadata.get(ZNTRACK_FIELD_LOAD)
        suffix = field.metadata.get(ZNTRACK_FIELD_SUFFIX)

        if getter is not None:
            if suffix is not None:
                return getter(self.node, field.name, suffix=suffix)
            return getter(self.node, field.name)
        return PLUGIN_EMPTY_RETRUN_VALUE

    def save(self, field: dataclasses.Field) -> None:
        dump_func = field.metadata.get(ZNTRACK_FIELD_DUMP)
        suffix = field.metadata.get(ZNTRACK_FIELD_SUFFIX)

        if dump_func is not None:
            if suffix is not None:
                dump_func(self.node, field.name, suffix=suffix)
            else:
                dump_func(self.node, field.name)

    def convert_to_params_yaml(self) -> dict | object:
        data = {}
        for field in dataclasses.fields(self.node):
            if field.metadata.get(FIELD_TYPE) == FieldTypes.PARAMS:
                data[field.name] = getattr(self.node, field.name)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.DEPS:
                if (value := deps_to_params(self, field)) is not None:
                    data[field.name] = value

        if len(data) > 0:
            return data
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_dvc_yaml(self) -> dict | object:
        node_dict = converter.NodeConverter().encode(self.node)

        cmd = f"zntrack run {node_dict['module']}.{node_dict['cls']}"
        cmd += f" --name {node_dict['name']}"
        if hasattr(self.node, "_method"):
            cmd += f" --method {self.node._method}"
        stages = {
            "cmd": cmd,
            "metrics": [
                {
                    (self.node.nwd / "node-meta.json").as_posix(): {
                        "cache": config.ALWAYS_CACHE
                    }
                }
            ],
        }
        if self.node.always_changed:
            stages["always_changed"] = True
        plots = []

        for field in dataclasses.fields(self.node):
            if field.metadata.get(FIELD_TYPE) == FieldTypes.PARAMS:
                stages.setdefault(FieldTypes.PARAMS.value, []).append(self.node.name)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.PARAMS_PATH:
                if len(content := params_path_to_dvc(self, field)) > 0:
                    stages.setdefault(FieldTypes.PARAMS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.OUTS_PATH:
                if len(content := outs_path_to_dvc(self, field)) > 0:
                    stages.setdefault(FieldTypes.OUTS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.PLOTS_PATH:
                if len(content := plots_path_to_dvc(self, field)) > 0:
                    stages.setdefault(FieldTypes.OUTS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.METRICS_PATH:
                if len(content := metrics_path_to_dvc(self, field)) > 0:
                    stages.setdefault(FieldTypes.METRICS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.OUTS:
                if len(content := outs_to_dvc(self, field)) > 0:
                    stages.setdefault(FieldTypes.OUTS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.PLOTS:
                suffix = field.metadata[ZNTRACK_FIELD_SUFFIX]
                content = [(self.node.nwd / field.name).with_suffix(suffix).as_posix()]
                if field.metadata.get(ZNTRACK_CACHE) is False:
                    content = [{c: {"cache": False}} for c in content]
                stages.setdefault(FieldTypes.OUTS.value, []).extend(content)
                if ZNTRACK_OPTION_PLOTS_CONFIG in field.metadata:
                    file_path = (
                        (self.node.nwd / field.name).with_suffix(suffix).as_posix()
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
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.METRICS:
                if len(content := metrics_to_dvc(self, field)) > 0:
                    stages.setdefault(FieldTypes.METRICS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.DEPS:
                deps_content, params_content = deps_to_dvc(self, field)
                if len(deps_content) > 0:
                    stages.setdefault(FieldTypes.DEPS.value, []).extend(deps_content)
                if len(params_content) > 0:
                    stages.setdefault(FieldTypes.PARAMS.value, []).extend(
                        params_content
                    )
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.DEPS_PATH:
                if len(content := deps_path_to_dvc(self, field)) > 0:
                    stages.setdefault(FieldTypes.DEPS.value, []).extend(content)

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
            if field.metadata.get(FIELD_TYPE) in [
                FieldTypes.PARAMS_PATH,
                FieldTypes.DEPS_PATH,
                FieldTypes.OUTS_PATH,
                FieldTypes.PLOTS_PATH,
                FieldTypes.METRICS_PATH,
                FieldTypes.DEPS,
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
