import importlib
import typing as t

import znflow
import znjson

from zntrack.config import ZNTRACK_OPTION, ZnTrackOptionEnum

from .node import Node
from .utils import module_handler


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


def node_to_output_paths(node: Node, attribute: str) -> t.List[str]:
    """Get all output paths for a node."""
    # What do we actually want as dependency?
    # paths = []
    # for field in dataclasses.fields(node):
    #     if field.metadata.get(_ZNTRACK_OPTION) == "outs":
    #         paths.append((node.nwd / field.name).with_suffix(".json").as_posix())
    # return paths
    if not node._unique_output_:
        return [(node.nwd / "node-meta.json").as_posix()]
    else:
        field = node.state.get_field(attribute)
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.OUTS:
            return [(node.nwd / f"{attribute}.json").as_posix()]
        else:
            raise NotImplementedError("Unique currently only implemented for outs")
