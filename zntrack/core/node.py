from __future__ import annotations

import znflow
import dataclasses
import enum
import pathlib
import zninit


class NodeStatusResults(enum.Enum):
    """The status of a node.

    Attributes
    ----------
    UNKNOWN : int
        No information is available.
    PENDING : int
        the Node instance is written to disk, but not yet run.
        `dvc stage add ` with the given parameters was run.
    RUNNING : int
        the Node instance is currently running.
        This state will be set when the run method is called.
    FINISHED : int
        the Node instance has finished running.
    FAILED : int
        the Node instance has failed to run.
    """

    UNKNOWN = 0
    PENDING = 1
    RUNNING = 2
    FINISHED = 3
    FAILED = 4


@dataclasses.dataclass
class NodeStatus:
    """The status of a node.

    Attributes
    ----------
    loaded : bool
        Whether the attributes of the Node are loaded from disk.
        If a new Node is created, this will be False.
    results : NodeStatusResults
        The status of the node results. E.g. was the computation successful.
    origin : str, default = "workspace"
        Where the Node has its data from. This could be the current "workspace" or
        a "remote" location, such as a git repository.
    rev : str, default = "HEAD"
        The revision of the Node. This could be the current "HEAD" or a specific revision.
    """

    loaded: bool
    results: "NodeStatusResults"
    origin: str = "workspace"
    rev: str = "HEAD"


class _NodeAttributes:
    """A mixin to sperate class attributes from class methods of a Node.

    Attributes
    ----------
    name : str, default = cls.__name__
        the Name of the Node
    state : NodeStatus
        information about the state of the Node.
    nwd : pathlib.Path
        the node working directory.
    """

    state: NodeStatus = NodeStatus(False, NodeStatusResults.UNKNOWN)
    _name: str

    @property
    def nwd(self) -> pathlib.Path:
        """Get the node working directory."""
        return pathlib.Path("nodes", znflow.get_attribute(self, "name"))

    @property
    def name(self) -> str:
        """Get the name of the node."""
        return znflow.get_attribute(self, "_name", self.__class__.__name__)


class Node(zninit.ZnInit, znflow.Node, _NodeAttributes):
    """A node in a ZnTrack workflow."""

    def save(self) -> None:
        """Save the node's output to disk."""

    def run(self) -> None:
        """Run the node's code."""

    def load(self) -> None:
        """Load the node's output from disk."""
        self.state.loaded = True
