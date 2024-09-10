import dataclasses
import importlib
import pathlib
import typing as t

import znflow
import znjson

from zntrack.config import (
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)

from .node import Node
from .utils import module_handler


def _enforce_str_list(content) -> list[str]:
    if isinstance(content, (str, pathlib.Path)):
        return [pathlib.Path(content).as_posix()]
    elif isinstance(content, (list, tuple)):
        return [pathlib.Path(x).as_posix() for x in content]
    else:
        raise ValueError(f"found unsupported content type '{content}'")


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
    # TODO: this should be a part of the DVCPlugin!
    if attribute is None:
        fields = dataclasses.fields(node)
    else:
        fields = [node.state.get_field(attribute)]
    paths = []
    for field in fields:
        option_type = field.metadata.get(ZNTRACK_OPTION)

        if any(
            option_type is x
            for x in [
                ZnTrackOptionEnum.PARAMS,
                ZnTrackOptionEnum.PARAMS,
                ZnTrackOptionEnum.DEPS,
                ZnTrackOptionEnum.DEPS_PATH,
                None,
            ]
        ):
            continue
        if field.metadata.get(ZNTRACK_INDEPENDENT_OUTPUT_TYPE) == True:
            paths.append((node.nwd / "node-meta.json").as_posix())
        if option_type == ZnTrackOptionEnum.OUTS:
            paths.append((node.nwd / f"{field.name}.json").as_posix())
        elif option_type == ZnTrackOptionEnum.PLOTS:
            paths.append((node.nwd / f"{field.name}.csv").as_posix())
        elif option_type == ZnTrackOptionEnum.METRICS:
            paths.append((node.nwd / f"{field.name}.json").as_posix())
        elif option_type == ZnTrackOptionEnum.OUTS_PATH:
            paths.extend(_enforce_str_list(getattr(node, field.name)))
        elif option_type == ZnTrackOptionEnum.PLOTS_PATH:
            paths.extend(_enforce_str_list(getattr(node, field.name)))
        elif option_type == ZnTrackOptionEnum.METRICS_PATH:
            paths.extend(_enforce_str_list(getattr(node, field.name)))

        if len(paths) == 0:
            raise ValueError(
                f"Unable to determine outputs for '{node.name}.{field.name}'."
            )

    return paths
