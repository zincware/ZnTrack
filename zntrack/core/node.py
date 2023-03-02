from __future__ import annotations

import dataclasses
import enum
import pathlib
import typing

import dvc.api
import znflow
import zninit

import zntrack.utils


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

    def get_file_system(self) -> dvc.api.DVCFileSystem:
        """Get the file system of the Node."""
        return dvc.api.DVCFileSystem(
            url=self.origin if self.origin != "workspace" else None,
            rev=self.rev if self.rev != "HEAD" else None,
        )


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
        # TODO do not have a save(results=True) method
        #   ensure, that parameters are NOT changed during the run.
        for attr in zninit.get_descriptors(self=self):
            attr.save(self)

    def run(self) -> None:
        """Run the node's code."""

    def load(self) -> None:
        """Load the node's output from disk."""
        for attr in zninit.get_descriptors(self=self):
            attr.load(self)
        self.state.loaded = True

    @classmethod
    def from_rev(cls, name=None, origin="workspace", rev="HEAD") -> Node:
        """Create a Node instance from an experiment."""
        node = cls.__new__(cls)
        if name is not None:
            node._name = name
        node.state = NodeStatus(False, NodeStatusResults.UNKNOWN, origin, rev)
        node.load()
        return node


def get_dvc_cmd(node: Node, force: bool = True) -> typing.List[str]:
    """Get the 'dvc stage add' command to run the node."""
    cmd = ["stage", "add"]
    cmd += ["--name", node.name]
    # TODO add all dvc stage extra parameters
    if force:
        cmd += ["--force"]
    field_cmds = []
    for attr in zninit.get_descriptors(self=node):
        field_cmds += attr.get_stage_add_argument(node)
    for field_cmd in set(field_cmds):
        cmd += list(field_cmd)

    module = zntrack.utils.module_handler(node.__class__)
    cmd += [f"zntrack run {module}.{node.__class__.__name__} --name {node.name}"]
    return cmd
