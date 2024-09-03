import dataclasses
import importlib
import pathlib
import typing as t
from collections import defaultdict

import znflow
import znjson

from .node import Node
from .options import ZNTRACK_CACHE, ZNTRACK_OPTION, ZnTrackOptionEnum
from .utils import get_attr_always_list, module_handler
from .utils.node_wd import NWDReplaceHandler


class NodeDict(t.TypedDict):
    module: str
    name: str
    cls: str
    remote: t.Optional[t.Any]
    rev: t.Optional[t.Any]


class NodeConverter(znjson.ConverterBase):

    level = 100
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

    def decode(self, s: dict) -> Node:
        module = importlib.import_module(s["module"])
        cls = getattr(module, s["cls"])
        return cls.from_rev(name=s["name"], remote=s["remote"], rev=s["rev"])


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


class CombinedConnectionsConverter(znjson.ConverterBase):
    """Convert a znflow.Connection object to dict and back."""

    level = 100
    representation = "znflow.CombinedConnections"
    instance = znflow.CombinedConnections

    def encode(self, obj: znflow.CombinedConnections) -> dict:
        """Convert the znflow.Connection object to dict."""
        if obj.item is not None:
            raise NotImplementedError(
                "znflow.CombinedConnections getitem is not supported yet."
            )
        return {
            "connections": obj.connections,
            "item": obj.item,
        }

    def decode(self, value: dict) -> znflow.CombinedConnections:
        """Create znflow.Connection object from dict."""
        return znflow.CombinedConnections(**value)


# zntrack.json


def convert_graph_to_zntrack_config(obj: znflow.DiGraph) -> dict:
    data = {}
    for node_uuid in obj:
        node = obj.nodes[node_uuid]["value"]
        data[node.name] = {
            "nwd": node.nwd,
        }
        for field in dataclasses.fields(node):
            if field.metadata.get(ZNTRACK_OPTION) in [
                ZnTrackOptionEnum.PARAMS,
                ZnTrackOptionEnum.OUTS,
                ZnTrackOptionEnum.PLOTS,
                ZnTrackOptionEnum.METRICS,
            ]:
                continue
            data[node.name][field.name] = node.__dict__[field.name]
    import warnings

    warnings.warn(f"saving {data}")
    return data


# dvc.yaml


def collect_paths(node, without_cache):
    """Collect and return paths that should not be cached."""
    paths = [
        (node.nwd / "metrics.json").as_posix(),
        (node.nwd / "node-meta.json").as_posix(),
    ]
    without_cache[node.name] = paths
    return paths


def handle_field_metadata(
    field: dataclasses.Field, node: Node, stages: dict, without_cache: dict, plots: dict
):
    """Process the field metadata to populate stages, without_cache, and plots."""
    field_option = field.metadata.get(ZNTRACK_OPTION)
    field_cached = field.metadata.get(ZNTRACK_CACHE)

    nwd_handler = NWDReplaceHandler()

    if field_option == ZnTrackOptionEnum.PARAMS:
        stages[node.name].setdefault(ZnTrackOptionEnum.PARAMS.value, []).append(node.name)

    elif field_option == ZnTrackOptionEnum.PARAMS_PATH:
        content = nwd_handler(get_attr_always_list(node, field.name), nwd=node.nwd)
        stages[node.name].setdefault(ZnTrackOptionEnum.PARAMS.value, []).extend(content)

    elif field_option == ZnTrackOptionEnum.OUTS_PATH:
        content = nwd_handler(get_attr_always_list(node, field.name), nwd=node.nwd)
        stages[node.name].setdefault(ZnTrackOptionEnum.OUTS.value, []).extend(content)
        if not field_cached:
            without_cache[node.name].extend(content)

    elif field_option == ZnTrackOptionEnum.PLOTS_PATH:
        content = nwd_handler(get_attr_always_list(node, field.name), nwd=node.nwd)
        stages[node.name].setdefault(ZnTrackOptionEnum.OUTS.value, []).extend(content)
        if not field_cached:
            without_cache[node.name].extend(content)
        plots[node.name] = None  # TODO

    elif field_option == ZnTrackOptionEnum.METRICS_PATH:
        content = nwd_handler(get_attr_always_list(node, field.name), nwd=node.nwd)
        stages[node.name].setdefault(ZnTrackOptionEnum.METRICS.value, []).extend(content)
        if not field_cached:
            without_cache[node.name].extend(content)

    elif field_option == ZnTrackOptionEnum.DEPS_PATH:
        content = [
            pathlib.Path(c).as_posix() for c in get_attr_always_list(node, field.name)
        ]
        stages[node.name].setdefault(ZnTrackOptionEnum.DEPS.value, []).extend(content)

    elif field_option == ZnTrackOptionEnum.METRICS:
        content = pathlib.Path(node.nwd, field.name).with_suffix(".json").as_posix()
        stages[node.name].setdefault(ZnTrackOptionEnum.METRICS.value, []).append(content)
        if not field_cached:
            without_cache[node.name].append(content)

    elif field_option == ZnTrackOptionEnum.OUTS:
        content = (node.nwd / field.name).with_suffix(".json").as_posix()
        stages[node.name].setdefault(ZnTrackOptionEnum.OUTS.value, []).append(content)
        if not field_cached:
            without_cache[node.name].append(content)

    elif field_option == ZnTrackOptionEnum.PLOTS:
        content = (node.nwd / field.name).with_suffix(".csv").as_posix()
        stages[node.name].setdefault(ZnTrackOptionEnum.OUTS.value, []).append(content)
        if not field_cached:
            without_cache[node.name].append(content)

    elif field_option == ZnTrackOptionEnum.DEPS:
        content = get_attr_always_list(node, field.name)
        paths = []
        for con in content:
            if isinstance(con, (znflow.Connection)):
                paths.extend(node_to_output_paths(con.instance))
            elif isinstance(con, (znflow.CombinedConnections)):
                for _con in con.connections:
                    paths.extend(node_to_output_paths(_con.instance))

        stages[node.name].setdefault(ZnTrackOptionEnum.DEPS.value, []).extend(paths)


def deduplicate_and_sort(stages, without_cache):
    """Ensure no duplicate paths and sort entries in stages."""
    for stage_name, stage in stages.items():
        without_caches = [pathlib.Path(x).as_posix() for x in without_cache[stage_name]]

        if ZnTrackOptionEnum.PARAMS in stage:
            paths = set(stage[ZnTrackOptionEnum.PARAMS])
            paths = {pathlib.Path(p).as_posix() for p in paths}
            stage[ZnTrackOptionEnum.PARAMS] = [
                path if path == stage_name else {path: None} for path in sorted(paths)
            ]

        if ZnTrackOptionEnum.OUTS in stage:
            paths = set(stage[ZnTrackOptionEnum.OUTS])
            paths = {pathlib.Path(p).as_posix() for p in paths}
            stage[ZnTrackOptionEnum.OUTS] = [
                {path: {"cache": False}} if path in without_caches else path
                for path in sorted(paths)
            ]

        if ZnTrackOptionEnum.METRICS in stage:
            paths = set(stage[ZnTrackOptionEnum.METRICS])
            paths = {pathlib.Path(p).as_posix() for p in paths}
            stage[ZnTrackOptionEnum.METRICS] = [
                {path: {"cache": False}} if path in without_caches else path
                for path in sorted(paths)
            ]


def convert_graph_to_dvc_config(obj: znflow.DiGraph) -> dict:
    """Build the stages dictionary from the given object."""
    stages = {}
    plots = {}
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
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
                if node.name not in data:
                    data[node.name] = {}
                data[node.name][field.name] = getattr(node, field.name)
    return data


def node_to_output_paths(node: Node) -> t.List[str]:
    """Get all output paths for a node."""
    # What do we actually want as dependency?
    # paths = []
    # for field in dataclasses.fields(node):
    #     if field.metadata.get(_ZNTRACK_OPTION) == "outs":
    #         paths.append((node.nwd / field.name).with_suffix(".json").as_posix())
    # return paths
    return [(node.nwd / "node-meta.json").as_posix()]
