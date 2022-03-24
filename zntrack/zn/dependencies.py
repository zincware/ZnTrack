from __future__ import annotations

import dataclasses
import pathlib
from typing import TYPE_CHECKING, List, Union

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
