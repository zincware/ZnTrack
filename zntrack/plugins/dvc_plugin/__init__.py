import dataclasses
import json
import logging
import typing as t

import znjson

from zntrack import config, converter
from zntrack.config import (
    FIELD_TYPE,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FIELD_SUFFIX,
    FieldTypes,
)

# if t.TYPE_CHECKING:
from zntrack.plugins import ZnTrackPlugin
from zntrack.plugins.dvc_plugin.dvc import (
    deps_path_to_dvc,
    deps_to_dvc,
    metrics_path_to_dvc,
    metrics_to_dvc,
    outs_path_to_dvc,
    outs_to_dvc,
    params_path_to_dvc,
    plots_path_to_dvc,
    plots_to_dvc,
)
from zntrack.plugins.dvc_plugin.params import deps_to_params
from zntrack.utils.misc import (
    sort_and_deduplicate,
)

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
                content = params_path_to_dvc(self, field)
                stages.setdefault(FieldTypes.PARAMS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.OUTS_PATH:
                content = outs_path_to_dvc(self, field)
                stages.setdefault(FieldTypes.OUTS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.PLOTS_PATH:
                content = plots_path_to_dvc(self, field)
                stages.setdefault(FieldTypes.OUTS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.METRICS_PATH:
                content = metrics_path_to_dvc(self, field)
                stages.setdefault(FieldTypes.METRICS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.OUTS:
                content = outs_to_dvc(self, field)
                stages.setdefault(FieldTypes.OUTS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.PLOTS:
                outs_content, plots_content = plots_to_dvc(self, field)
                stages.setdefault(FieldTypes.OUTS.value, []).extend(outs_content)
                plots.extend(plots_content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.METRICS:
                content = metrics_to_dvc(self, field)
                stages.setdefault(FieldTypes.METRICS.value, []).extend(content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.DEPS:
                deps_content, params_content = deps_to_dvc(self, field)
                stages.setdefault(FieldTypes.DEPS.value, []).extend(deps_content)
                stages.setdefault(FieldTypes.PARAMS.value, []).extend(params_content)
            elif field.metadata.get(FIELD_TYPE) == FieldTypes.DEPS_PATH:
                content = deps_path_to_dvc(self, field)
                stages.setdefault(FieldTypes.DEPS.value, []).extend(content)

        for key in list(stages):
            if key not in ["cmd", "always_changed"]:
                if len(stages[key]) == 0:
                    del stages[key]
                else:
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
