import dataclasses
import pathlib
import typing as t

import znflow
import znjson

from .node import Node
from .utils import get_attr_always_list, module_handler, replace_nwd_placeholder
from .options import _ZNTRACK_OPTION, _ZNTRACK_CACHE


class NodeDict(t.TypedDict):
    module: str
    name: str
    cls: str
    remote: t.Optional[t.Any]
    rev: t.Optional[t.Any]


class NodeConverter(znjson.ConverterBase):
    instance = Node
    representation = "zntrack.Node"

    def encode(self, obj: Node) -> NodeDict:
        return {
            "module": module_handler(obj),
            "name": obj.name,
            "cls": obj.__class__.__name__,
            "remote": None,
            "rev": None,
        }

    def decode(self, s: str) -> None:
        return None


class ConnectionConverter(znjson.ConverterBase):
    """Convert a znflow.Connection object to dict and back."""

    level = 100
    representation = "znflow.Connection"
    instance = znflow.Connection

    def encode(self, obj: znflow.Connection) -> dict:
        """Convert the znflow.Connection object to dict."""
        if obj.item is not None:
            raise NotImplementedError("znflow.Connection getitem is not supported yet.")
        # Can not use `dataclasses.asdict` because it automatically converts nested dataclasses to dict.
        return {
            "instance": obj.instance,
            "attribute": obj.attribute,
            "item": obj.item,
        }

    def decode(self, value: dict) -> znflow.Connection:
        """Create znflow.Connection object from dict."""
        return znflow.Connection(**value)


# zntrack.json


def convert_graph_to_zntrack_config(obj: znflow.DiGraph) -> dict:
    data = {}
    for node_uuid in obj:
        node = obj.nodes[node_uuid]["value"]
        data[node.name] = {
            "nwd": node.nwd,
        }
        for field in dataclasses.fields(node):
            if field.metadata.get(_ZNTRACK_OPTION) in [
                "params",
                "outs",
                "plots",
                "metrics",
            ]:
                continue
            data[node.name][field.name] = getattr(node, field.name)
    return data


# dvc.yaml
from collections import defaultdict
import pathlib
import dataclasses


def collect_paths(node, without_cache):
    """Collect and return paths that should not be cached."""
    paths = [
        (node.nwd / "metrics.json").as_posix(),
        (node.nwd / "node-meta.json").as_posix(),
    ]
    without_cache[node.name] = paths
    return paths


def handle_field_metadata(field, node, stages, without_cache, plots):
    """Process the field metadata to populate stages, without_cache, and plots."""
    field_option = field.metadata.get(_ZNTRACK_OPTION)
    field_cached = field.metadata.get(_ZNTRACK_CACHE)

    if field_option == "params":
        stages[node.name].setdefault("params", []).append(node.name)

    elif field_option == "params_path":
        stages[node.name].setdefault("params", []).extend(
            [
                replace_nwd_placeholder(c, node.nwd)
                for c in get_attr_always_list(node, field.name)
            ]
        )

    elif field_option in {"outs_path", "plots_path"}:
        content = [
            replace_nwd_placeholder(c, node.nwd)
            for c in get_attr_always_list(node, field.name)
        ]
        stages[node.name].setdefault("outs", []).extend(content)
        if not field_cached:
            without_cache[node.name].extend(content)
        if field_option == "plots_path":
            plots.extend(content)

    elif field_option == "metrics_path":
        content = [
            replace_nwd_placeholder(c, node.nwd)
            for c in get_attr_always_list(node, field.name)
        ]
        stages[node.name].setdefault("metrics", []).extend(content)
        if not field_cached:
            without_cache[node.name].extend(content)

    elif field_option == "metrics":
        stages[node.name].setdefault("metrics", []).append(
            pathlib.Path(node.nwd, "metrics.json").as_posix()
        )

    elif field_option == "outs":
        stages[node.name].setdefault("outs", []).append(
            (node.nwd / field.name).with_suffix(".json").as_posix()
        )

    elif field_option == "deps_path":
        stages[node.name].setdefault("deps", []).append(getattr(node, field.name))

    elif field_option == "deps":
        data = getattr(node, field.name)
        stages[node.name].setdefault("deps", []).extend(
            node_to_output_paths(con.instance) for con in data if isinstance(data, list)
        )


def deduplicate_and_sort(stages, without_cache):
    """Ensure no duplicate paths and sort entries in stages."""
    for stage_name, stage in stages.items():
        if "params" in stage:
            stage["params"] = [
                path if path == stage_name else {path: None}
                for path in sorted(set(stage["params"]))
            ]

        if "outs" in stage:
            stage["outs"] = [
                {path: {"cache": False}} if path in without_cache[stage_name] else path
                for path in sorted(set(stage["outs"]))
            ]

        if "metrics" in stage:
            stage["metrics"] = [
                {path: {"cache": False}} if path in without_cache[stage_name] else path
                for path in sorted(set(stage["metrics"]))
            ]


def convert_graph_to_dvc_config(obj: znflow.DiGraph) -> dict:
    """Build the stages dictionary from the given object."""
    stages = {}
    plots = []
    without_cache = defaultdict(list)

    for node_uuid in obj:
        node: Node = obj.nodes[node_uuid]["value"]
        collect_paths(node, without_cache)

        node_dict = NodeConverter().encode(node)
        stages[node.name] = {
            "cmd": f"zntrack run {node_dict['module']}.{node_dict['cls']} --name {node_dict['name']}",
            "metrics": [(node.nwd / "node-meta.json").as_posix()],
        }

        for field in dataclasses.fields(node):
            handle_field_metadata(field, node, stages, without_cache, plots)

    deduplicate_and_sort(stages, without_cache)
    return {"stages": stages}


# params.yaml
def convert_graph_to_parameter(obj: znflow.DiGraph) -> dict:
    data = {}
    for node_uuid in obj:
        node: Node = obj.nodes[node_uuid]["value"]
        for field in dataclasses.fields(node):
            if field.metadata.get("zntrack.option") == "params":
                if node.name not in data:
                    data[node.name] = {}
                data[node.name][field.name] = getattr(node, field.name)
    return data


def node_to_output_paths(node: Node) -> t.List[str]:
    """Get all output paths for a node."""
    paths = []
    for field in dataclasses.fields(node):
        if field.metadata.get("zntrack.option") == "outs":
            paths.append((node.nwd / field.name).with_suffix(".json").as_posix())
    return paths
