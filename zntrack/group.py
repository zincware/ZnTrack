import typing as t

import znflow

if t.TYPE_CHECKING:
    from zntrack import Node


class Group:
    def __init__(self, name: tuple[str], nodes: list | None = None) -> None:
        self._name = name
        self._nodes = nodes if nodes else []

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

    def __contains__(self, item: "Node") -> bool:
        """Check if the Node is in the group."""
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

    def get_node_name(self, node: "Node") -> str:
        """Get the node name with group prefix."""
        if node not in self:
            raise ValueError(f"Node {node} is not part of {self}")
        if node.name is None:
            return f"{'_'.join(self._name)}_{node.__class__.__name__}"
        return f"{'_'.join(self._name)}_{node.name}"