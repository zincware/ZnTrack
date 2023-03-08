"""The Node class."""
from __future__ import annotations

import dataclasses
import importlib
import logging
import pathlib
import typing

import dvc.api
import dvc.cli
import znflow
import zninit
import znjson

from zntrack.utils import NodeStatusResults, deprecated, module_handler, run_dvc_cmd

log = logging.getLogger(__name__)


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
    origin : str, default = None
        Where the Node has its data from. This could be the current "workspace" or
        a "remote" location, such as a git repository.
    rev : str, default = None
        The revision of the Node. This could be the current "HEAD" or a specific revision.
    """

    loaded: bool
    results: "NodeStatusResults"
    origin: str = None
    rev: str = None

    def get_file_system(self) -> dvc.api.DVCFileSystem:
        """Get the file system of the Node."""
        return dvc.api.DVCFileSystem(
            url=self.origin,
            rev=self.rev,
        )


class _NameDescriptor(zninit.Descriptor):
    """A descriptor for the name attribute."""

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if getattr(instance, "_name_") is None:
            instance._name_ = instance.__class__.__name__
        return getattr(instance, "_name_")

    def __set__(self, instance, value):
        if value is None:
            return
        instance._name_ = value


class Node(zninit.ZnInit, znflow.Node):
    """A node in a ZnTrack workflow.

    Attributes
    ----------
    name : str, default = cls.__name__
        the Name of the Node
    state : NodeStatus
        information about the state of the Node.
    nwd : pathlib.Path
        the node working directory.
    """

    _state: NodeStatus = None

    name: str = _NameDescriptor(None)
    _name_ = None

    @property
    def _init_descriptors_(self):
        from zntrack import fields

        return [
            fields.zn.Params,
            fields.zn.Dependency,
            fields.meta.Text,
            fields.dvc.DVCOption,
            _NameDescriptor,
        ]

    @property
    def state(self) -> NodeStatus:
        """Get the state of the node."""
        if self._state is None:
            self._state = NodeStatus(False, NodeStatusResults.UNKNOWN)
        return self._state

    @property
    def nwd(self) -> pathlib.Path:
        """Get the node working directory."""
        nwd = pathlib.Path("nodes", znflow.get_attribute(self, "name"))
        if not nwd.exists():
            nwd.mkdir(parents=True)
        return nwd

    def save(self) -> None:
        """Save the node's output to disk."""
        # TODO have an option to save and run dvc commit afterwards.
        from zntrack.fields.field import Field

        for attr in zninit.get_descriptors(Field, self=self):
            attr.save(self)

    def run(self) -> None:
        """Run the node's code."""

    def load(self) -> None:
        """Load the node's output from disk."""
        from zntrack.fields.field import Field

        for attr in zninit.get_descriptors(Field, self=self):
            attr.load(self)

        self.state.loaded = True

    @classmethod
    def from_rev(cls, name=None, origin=None, rev=None) -> Node:
        """Create a Node instance from an experiment."""
        node = cls.__new__(cls)
        node.name = name
        node._state = NodeStatus(False, NodeStatusResults.UNKNOWN, origin, rev)
        node_identifier = NodeIdentifier(
            module_handler(cls), cls.__name__, node.name, origin, rev
        )
        log.debug(f"Creating {node_identifier}")
        node.load()
        return node

    @deprecated(
        "Building a graph is now done using 'with zntrack.Project() as project: ...'",
        version="0.6.0",
    )
    def write_graph(self, run: bool = False, **kwargs):
        """Write the graph to dvc.yaml."""
        cmd = get_dvc_cmd(self, **kwargs)
        for x in cmd:
            run_dvc_cmd(x)
        self.save()

        if run:
            run_dvc_cmd(["repro", self.name])


def get_dvc_cmd(
    node: Node,
    quiet: bool = False,
    verbose: bool = False,
    force: bool = True,
    external: bool = False,
    always_changed: bool = False,
    desc: str = None,
) -> typing.List[typing.List[str]]:
    """Get the 'dvc stage add' command to run the node."""
    from zntrack.fields.field import Field

    optionals = []

    cmd = ["stage", "add"]
    cmd += ["--name", node.name]
    if quiet:
        cmd += ["--quiet"]
    if verbose:
        cmd += ["--verbose"]
    if force:
        cmd += ["--force"]
    if external:
        cmd += ["--external"]
    if always_changed:
        cmd += ["--always-changed"]
    if desc:
        cmd += ["--desc", desc]
    field_cmds = []
    for attr in zninit.get_descriptors(Field, self=node):
        field_cmds += attr.get_stage_add_argument(node)
        optionals.append(attr.get_optional_dvc_cmd(node))
    for field_cmd in set(field_cmds):
        cmd += list(field_cmd)

    module = module_handler(node.__class__)
    cmd += [f"zntrack run {module}.{node.__class__.__name__} --name {node.name}"]
    optionals = [x for x in optionals if x]  # remove empty entries []
    return [cmd] + optionals


@dataclasses.dataclass
class NodeIdentifier:
    """All information that uniquly identifies a node."""

    module: str
    cls: str
    name: str
    origin: str
    rev: str

    @classmethod
    def from_node(cls, node: Node):
        """Create a _NodeIdentifier from a Node object."""
        return cls(
            module=module_handler(node),
            cls=node.__class__.__name__,
            name=node.name,
            origin=node.state.origin,
            rev=node.state.rev,
        )

    def get_node(self) -> Node:
        """Get the node from the identifier."""
        module = importlib.import_module(self.module)
        cls = getattr(module, self.cls)
        return cls.from_rev(name=self.name, origin=self.origin, rev=self.rev)


class NodeConverter(znjson.ConverterBase):
    """A converter for the Node class."""

    level = 100
    representation = "zntrack.Node"
    instance = Node

    def encode(self, obj: Node) -> dict:
        """Convert the Node object to dict."""
        node_identifier = NodeIdentifier.from_node(obj)
        if node_identifier.rev is not None:
            raise NotImplementedError(
                "Dependencies to other revisions are not supported yet"
            )

        return dataclasses.asdict(node_identifier)

    def decode(self, value: dict) -> Node:
        """Create Node object from dict."""
        # TODO if rev = HEAD, replace with the rev from the 'Node.from_rev'
        return NodeIdentifier(**value).get_node()


znjson.config.register(NodeConverter)