"""ZnTrack dependencies."""
from __future__ import annotations

import dataclasses
import importlib
import inspect
import pathlib
from typing import TYPE_CHECKING, List, Set, Union

import znjson

from zntrack.utils import utils

if TYPE_CHECKING:
    from zntrack import Node


@dataclasses.dataclass
class NodeAttribute:
    """ZnTrack NodeAttribute."""

    module: str
    cls: str
    name: str
    attribute: str

    # Not dataclass related attributes. See https://peps.python.org/pep-0557/#id7
    _node = None

    @property
    def affected_files(self) -> Set[pathlib.Path]:
        """Get a list of all affected files."""
        if self._node is None:
            module = importlib.import_module(self.module)
            cls = getattr(module, self.cls)
            self._node = cls.load(self.name)
        return self._node.affected_files


class RawNodeAttributeConverter(znjson.ConverterBase):
    """Serializer for Node Attributes.

    Instead of returning the actual attribute this returns the NodeAttribute cls.
    """

    instance = NodeAttribute
    representation = "NodeAttribute"
    level = 999

    def encode(self, obj: NodeAttribute) -> dict:
        """Convert NodeAttribute to serializable dict."""
        return dataclasses.asdict(obj)

    def decode(self, value: dict) -> NodeAttribute:
        """return serialized Node attribute."""
        return NodeAttribute(**value)


def getdeps(node: Union[Node, type(Node)], attribute: str) -> NodeAttribute:
    """Allow for Node attributes as dependencies."""
    # TODO add check if the attribute exists in the given Node
    # _ = getattr(node, attribute)
    node = utils.load_node_dependency(node)  # run node = Node.load() if required
    return NodeAttribute(
        module=node.module,
        cls=node.__class__.__name__,
        name=node.node_name,
        attribute=attribute,
    )


def get_origin(
    node: Union[Node, type(Node)], attribute: str
) -> Union[NodeAttribute, List[NodeAttribute]]:
    """Get the NodeAttribute from a zn.deps.

    Typically, when using zn.deps there is no way to access the original Node where
    the data comes from. This function allows you to get the underlying
    NodeAttribute object to access e.g. the name of the original Node.

    Raises
    ------
    AttributeError: if the attribute is not of type zn.deps
    """
    znjson.config.register(RawNodeAttributeConverter)
    node_name = None if inspect.isclass(node) else node.node_name
    new_node = node.load(name=node_name)
    value = getattr(new_node, attribute)

    znjson.config.deregister(RawNodeAttributeConverter)

    def not_zn_deps_err() -> AttributeError:
        """Evaluate error message when raising the error."""
        return AttributeError(
            f"'{new_node.node_name}' object has no attribute '{attribute}' of type"
            f" 'zn.deps'. Found {type(getattr(node.__class__, attribute))} instead"
        )

    if isinstance(value, (list, tuple)):
        for entry in value:
            if not isinstance(entry, NodeAttribute):
                raise not_zn_deps_err()
    elif not isinstance(value, NodeAttribute):
        raise not_zn_deps_err()
    return value
