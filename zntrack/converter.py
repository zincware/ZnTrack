import dataclasses
import typing as t

import znflow
import znjson

from .node import Node
from .utils import module_handler


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
    for node_uuid in obj:
        node: Node = obj.nodes[node_uuid]["value"]

        node_dict = NodeConverter().encode(node)

        stages[node.name] = {
            "cmd": f"zntrack run {node_dict['module']}.{node_dict['cls']} --name {node_dict['name']}",
        }
        for field in dataclasses.fields(node):
            if field.metadata.get("zntrack.option") == "params":
                if "params" not in stages[node.name]:
                    stages[node.name]["params"] = []
                stages[node.name]["params"].append(node.name)

            if field.metadata.get("zntrack.option") == "outs_path":
                if "outs" not in stages[node.name]:
                    stages[node.name]["outs"] = []
                # TODO: handle pathlib, lists, dicts, etc.
                stages[node.name]["outs"].append(getattr(node, field.name))

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
        if "params" in stages[node.name]:
            stages[node.name]["params"] = list(set(stages[node.name]["params"]))
        if "outs" in stages[node.name]:
            # TODO: handle pathlib, lists, dicts, etc.
            pass

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
