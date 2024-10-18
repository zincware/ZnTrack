import pathlib
import typing as t

import znflow

from zntrack.config import NWD_PATH

if t.TYPE_CHECKING:
    from zntrack import Node


def _extract_group_from_nwd(path: pathlib.Path) -> tuple | None:
    # Convert the path to a list of parts
    parts = list(path.parts)

    # Check if the path starts with 'nodes'
    if parts[0] != str(NWD_PATH):
        raise ValueError(f"Path must start with 'nodes', found {parts}")

    # Check the length of the path to determine the output
    if len(parts) == 2:  # no groups
        return None
    else:  # groups
        return tuple(parts[1:-1])


class Group:
    def __init__(self, name: tuple[str], nodes: list | None = None) -> None:
        self._name = name
        self._nodes = nodes if nodes else []

    @property
    def nwd(self) -> pathlib.Path:
        return NWD_PATH.joinpath(*self._name)

    @property
    def name(self):
        return self._name

    @property
    def nodes(self):
        return self._nodes

    def __eq__(self, value: "Group") -> bool:
        if not isinstance(value, self.__class__):
            return False
        return value.name == self.name

    def __repr__(self) -> str:
        return f"Group(name='{self._name}')"

    def __str__(self) -> str:
        return f"Group(name='{self._name}')"

    def __contains__(self, item: "Node|str") -> bool:
        """Check if the Node is in the group."""
        if isinstance(item, str):
            return item in [node.name for node in self._nodes]
        return item in self._nodes

    def __iter__(self) -> t.Iterator["Node"]:
        """Iterate over the nodes in the group."""
        return iter(self._nodes)

    def __getitem__(self, name: str) -> "Node":
        """Get the Node from the group."""
        for node in self._nodes:
            if node.name == name:
                return node
        raise KeyError(f"Node {name} not found.")

    def __len__(self) -> int:
        """Get the number of nodes in the group."""
        return len(self._nodes)

    @classmethod
    def from_znflow_group(cls, group: znflow.Group) -> "Group":
        return cls(name=group.names, nodes=group.nodes)

    @classmethod
    def from_nwd(cls, nwd: pathlib.Path) -> "Group|None":
        names = _extract_group_from_nwd(nwd)
        if names is None:
            return None
        return cls(name=names)
