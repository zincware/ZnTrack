import dataclasses
import pathlib
import typing as t
import znflow

if t.TYPE_CHECKING:
    from zntrack import Node


@dataclasses.dataclass
class Group:
    name: tuple[str]
    # nwd: pathlib.Path
    nodes: list["Node"] = dataclasses.field(default_factory=list)

    def __contains__(self, item: "Node") -> bool:
        """Check if the Node is in the group."""
        return item in self.nodes

    def __iter__(self) -> t.Iterator["Node"]:
        """Iterate over the nodes in the group."""
        return iter(self.nodes)

    def __getitem__(self, name: int) -> "Node":
        """Get the Node from the group."""
        raise NotImplementedError
        raise KeyError(f"Node {name} not in group {self.name}")

    def __len__(self) -> int:
        """Get the number of nodes in the group."""
        return len(self.nodes)
    
    @classmethod
    def from_znflow_group(cls, group: znflow.Group) -> "Group":
        return cls(
            name=group.names,
            nodes=group.nodes
        )
    

    def get_node_name(self, node: "Node") -> str:
        """Get the node name with group prefix."""
        if node not in self:
            raise ValueError(f"Node {node} is not part of {self}")
        if node.name is None:
            return f"{'_'.join(self.name)}_{node.__class__.__name__}"
        return f"{'_'.join(self.name)}_{node.name}"
    
