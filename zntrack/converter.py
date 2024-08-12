import dataclasses
import pathlib
import typing as t

import znflow
import znjson

from .node import Node
from .utils import get_attr_always_list, module_handler, replace_nwd_placeholder


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
            if field.metadata.get("zntrack.option") in [
                "params",
                "outs",
                "plots",
                "metrics",
            ]:
                continue
            data[node.name][field.name] = getattr(node, field.name)
    return data


# dvc.yaml
def convert_graph_to_dvc_config(obj: znflow.DiGraph) -> dict:
    stages = {}
    plots = []
    without_cache: dict[str, list[str]] = {}  # paths that should use --no-cache
    for node_uuid in obj:
        node: Node = obj.nodes[node_uuid]["value"]
        without_cache[node.name] = [
            # (node.nwd / "outs.json").as_posix(),
            (node.nwd / "metrics.json").as_posix(),
            # (node.nwd / "plots.csv").as_posix(),
            (node.nwd / "node-meta.json").as_posix(),
        ]

        node_dict = NodeConverter().encode(node)

        stages[node.name] = {
            "cmd": f"zntrack run {node_dict['module']}.{node_dict['cls']} --name {node_dict['name']}",
        }
        stages[node.name]["metrics"] = [(node.nwd / "node-meta.json").as_posix()]

        for field in dataclasses.fields(node):

            if field.metadata.get("zntrack.option") == "params":
                if "params" not in stages[node.name]:
                    stages[node.name]["params"] = []
                stages[node.name]["params"].append(node.name)

            if field.metadata.get("zntrack.option") == "params_path":
                pass  # `file:` or `file:key`

            if field.metadata.get("zntrack.option") == "outs_path":
                if "outs" not in stages[node.name]:
                    stages[node.name]["outs"] = []
                # TODO: handle pathlib, lists, dicts, etc.
                content = get_attr_always_list(node, field.name)
                content = [replace_nwd_placeholder(c, node.nwd) for c in content]
                stages[node.name]["outs"].extend(content)
                if field.metadata.get("zntrack.no_cache"):
                    without_cache[node.name].extend(content)

            if field.metadata.get("zntrack.option") == "plots_path":
                if "outs" not in stages[node.name]:
                    stages[node.name]["outs"] = []
                content = get_attr_always_list(node, field.name)
                content = [replace_nwd_placeholder(c, node.nwd) for c in content]
                stages[node.name]["outs"].extend(content)
                if field.metadata.get("zntrack.no_cache"):
                    without_cache[node.name].extend(content)

                plots.extend(content)  # update plots options

            if field.metadata.get("zntrack.option") == "metrics_path":
                if "metrics" not in stages[node.name]:
                    stages[node.name]["metrics"] = []
                content = get_attr_always_list(node, field.name)
                content = [replace_nwd_placeholder(c, node.nwd) for c in content]
                stages[node.name]["metrics"].extend(content)
                if field.metadata.get("zntrack.no_cache"):
                    without_cache[node.name].extend(content)

            if field.metadata.get("zntrack.option") == "metrics":
                if "metrics" not in stages[node.name]:
                    stages[node.name]["metrics"] = []
                stages[node.name]["metrics"].append(
                    pathlib.Path(node.nwd, "metrics.json").as_posix()
                )

            if field.metadata.get("zntrack.option") == "outs":
                if "outs" not in stages[node.name]:
                    stages[node.name]["outs"] = []
                stages[node.name]["outs"].append(
                    (node.nwd / field.name).with_suffix(".json").as_posix()
                )
            if field.metadata.get("zntrack.option") == "deps_path":
                if "deps" not in stages[node.name]:
                    stages[node.name]["deps"] = []
                stages[node.name]["deps"].append(getattr(node, field.name))
            if field.metadata.get("zntrack.option") == "deps":
                if "deps" not in stages[node.name]:
                    stages[node.name]["deps"] = []
                data = getattr(node, field.name)
                if isinstance(data, list):
                    for con in data:
                        # we need a good way to find the things we actually want to depend on:
                        # either just the `node-meta` which is sufficient
                        # or specify specifig outs to avoid re-running stage
                        stages[node.name]["deps"].extend(
                            node_to_output_paths(con.instance)
                        )

        # ensure no duplicates
        # if "params" in stages[node.name]:
        # stages[node.name]["params"] = list(set(stages[node.name]["params"]))

        stages[node.name]["params"].append({"parameter.yaml": None})

        if "outs" in stages[node.name]:
            content = set(stages[node.name]["outs"])
            stages[node.name]["outs"] = []
            for path in sorted(content):
                if path in without_cache[node.name]:
                    stages[node.name]["outs"].append({path: {"cache": False}})
                else:
                    stages[node.name]["outs"].append(path)
        if "metrics" in stages[node.name]:
            content = set(stages[node.name]["metrics"])
            stages[node.name]["metrics"] = []
            for path in sorted(content):
                if path in without_cache[node.name]:
                    stages[node.name]["metrics"].append({path: {"cache": False}})
                else:
                    stages[node.name]["metrics"].append(path)

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
