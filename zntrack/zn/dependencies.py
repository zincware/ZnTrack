import dataclasses
import pathlib
from typing import List, Protocol, Set

from zntrack.utils import utils


@dataclasses.dataclass
class NodeAttribute:
    module: str
    cls: str
    name: str
    attribute: str
    affected_files: Set[pathlib.Path]


class TypeNode(Protocol):
    """Duck type typehints for Node"""

    @property
    def module(self) -> str:
        ...

    @property
    def node_name(self) -> str:
        ...

    @property
    def affected_files(self) -> List[pathlib.Path]:
        ...


def getdeps(node: TypeNode, attribute: str) -> NodeAttribute:
    """Allow for Node attributes as dependencies

    Parameters
    ----------
    node
    attribute

    Returns
    -------

    """
    node = utils.load_node_dependency(node)  # run node = Node.load() if required
    return NodeAttribute(
        module=node.module,
        cls=node.__class__.__name__,
        name=node.node_name,
        attribute=attribute,
        affected_files=list(node.affected_files),
    )
