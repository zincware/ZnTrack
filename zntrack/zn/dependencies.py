from __future__ import annotations

import dataclasses
import pathlib
from typing import TYPE_CHECKING, List, Union

import znjson

from zntrack.utils import utils

if TYPE_CHECKING:
    from zntrack import Node


@dataclasses.dataclass
class NodeAttribute:
    module: str
    cls: str
    name: str
    attribute: str
    affected_files: List[pathlib.Path]


class RawNodeAttributeConverter(znjson.ConverterBase):
    """Serializer for Node Attributes

    Instead of returning the actual attribute this returns the NodeAttribute cls.
    """

    instance = NodeAttribute
    representation = "NodeAttribute"
    level = 999

    def _encode(self, obj: NodeAttribute) -> dict:
        """Convert NodeAttribute to serializable dict"""
        return dataclasses.asdict(obj)

    def _decode(self, value: dict) -> NodeAttribute:
        """return serialized Node attribute"""
        return NodeAttribute(**value)


def getdeps(node: Union[Node, type(Node)], attribute: str) -> NodeAttribute:
    """Allow for Node attributes as dependencies

    Parameters
    ----------
    node
    attribute

    Returns
    -------

    """
    # TODO add check if the attribute exists in the given Node
    # _ = getattr(node, attribute)
    node = utils.load_node_dependency(node)  # run node = Node.load() if required
    return NodeAttribute(
        module=node.module,
        cls=node.__class__.__name__,
        name=node.node_name,
        attribute=attribute,
        affected_files=list(node.affected_files),
    )


def get_origin(
    node: Union[Node, type(Node)], attribute: str
) -> Union[NodeAttribute, List[NodeAttribute]]:
    """Get the NodeAttribute from a zn.deps

    Typically, when using zn.deps there is no way to access the original Node where
    the data comes from. This function allows you to get the underlying
    NodeAttribute object to access e.g. the name of the original Node.
    """
    znjson.register(RawNodeAttributeConverter)
    new_node = node.load(name=node.node_name)
    try:
        value = getattr(new_node, attribute)
    except AttributeError as err:
        raise AttributeError("Can only use get_origin with zn.deps") from err
    znjson.deregister(RawNodeAttributeConverter)

    if isinstance(value, (list, tuple)):
        if any([not isinstance(x, NodeAttribute) for x in value]):
            raise AttributeError("Can only use get_origin with zn.deps using getdeps.")
    elif not isinstance(value, NodeAttribute):
        raise AttributeError("Can only use get_origin with zn.deps using getdeps.")
    return value
