"""The class for the ZnTrackProject."""
from __future__ import annotations

import contextlib
import dataclasses
import json
import logging
import pathlib
import shutil
import subprocess
import typing

import dvc.api
import git
import yaml
import znflow
from znflow.base import empty, get_graph
from znflow.handler import UpdateConnectors

from zntrack import exceptions
from zntrack.core.node import Node, get_dvc_cmd
from zntrack.utils import run_dvc_cmd

log = logging.getLogger(__name__)


def _initalize():
    """Initialize the project."""
    try:
        _ = git.Repo()
    except git.exc.InvalidGitRepositoryError:
        # TODO ASSERT IS EMPTY!
        repo = git.Repo.init()
        repo.init()
        run_dvc_cmd(["init", "--quiet"])
        # Create required files:
        pathlib.Path("zntrack.json").write_text(json.dumps({}))
        pathlib.Path("dvc.yaml").write_text(yaml.safe_dump({}))
        pathlib.Path("params.yaml").write_text(yaml.safe_dump({}))
        repo.git.add(A=True)
        repo.index.commit("Project initialized.")


class ZnTrackGraph(znflow.DiGraph):
    """Subclass of the znflow.DiGraph."""

    project: Project = None

    def add_node(self, node_for_adding, **attr):
        """Rename Nodes if required."""
        value = super().add_node(node_for_adding, **attr)
        self.project.update_node_names(check=False)
        # this is called in __new__ and therefore,
        # the name might not be set correctly.
        # update node names only works, if name is not set.
        return value


@dataclasses.dataclass
class Project:
    """The ZnTrack Project class.

    Attributes
    ----------
    graph : znflow.DiGraph
        the znflow graph of the project.
    initialize : bool, default = True
        If True, initialize a git repository and a dvc repository.
    remove_existing_graph : bool, default = False
        If True, remove 'dvc.yaml', 'zntrack.json' and 'params.yaml'
            before writing new nodes.
    automatic_node_names : bool, default = False
        If True, automatically add a number to the node name if the name is already
            used in the graph.
    git_only_repo : bool, default = True
        The DVC graph relies on file outputs for connecting stages.
        ZnTrack will use a '--metrics-no-cache' file output for each stage by default.
        Contrary to '--outs-no-cache', this will keep the DVC run cache available.
        If a project has a DVC remote available, '--outs' can be used instead.
        This will require a DVC remote to be setup.
    force : bool, default = False
        overwrite existing nodes.
    """

    graph: znflow.DiGraph = dataclasses.field(default_factory=ZnTrackGraph, init=False)
    initialize: bool = True
    remove_existing_graph: bool = False
    automatic_node_names: bool = False
    git_only_repo: bool = True
    force: bool = False

    _groups: list = dataclasses.field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Initialize the Project.

        Attributes
        ----------
        initialize : bool, default = True
            If True, initialize a git repository and a dvc repository.
        remove_existing_graph : bool, default = False
            If True, remove 'dvc.yaml', 'zntrack.json' and 'params.yaml'
              before writing new nodes.
        """
        self.graph.project = self
        if self.initialize:
            _initalize()
        if self.remove_existing_graph:
            # we remove the files that typically contain the graph definition
            pathlib.Path("zntrack.json").unlink(missing_ok=True)
            pathlib.Path("dvc.yaml").unlink(missing_ok=True)
            pathlib.Path("params.yaml").unlink(missing_ok=True)
            shutil.rmtree("nodes", ignore_errors=True)

    def __enter__(self, *args, **kwargs):
        """Enter the graph context."""
        self.graph.__enter__(*args, **kwargs)
        return self

    def __exit__(self, *args, **kwargs):
        """Exit the graph context."""
        self.graph.__exit__(*args, **kwargs)
        self.update_node_names()

    def update_node_names(self, check=True):
        """Update the node names to be unique."""
        node_names = []
        for node_uuid in self.graph.get_sorted_nodes():
            node: Node = self.graph.nodes[node_uuid]["value"]
            if node.name in node_names:
                if node._external_:
                    continue
                if self.automatic_node_names:
                    idx = 1
                    while f"{node.name}_{idx}" in node_names:
                        idx += 1
                    node.name = f"{node.name}_{idx}"
                    log.debug(f"Updating {node.name = }")

                elif not self.force and check:
                    raise exceptions.DuplicateNodeNameError(node)
            node_names.append(node.name)

    @contextlib.contextmanager
    def group(self, *names: typing.List[str]):
        """Group nodes together.

        Parameters
        ----------
        names : list[str], optional
            The name of the group. If None, the group will be named 'GroupX' where X is
            the number of groups + 1. If more than one name is given, the groups will
            be nested to 'nwd = name[0]/name[1]/.../name[-1]'
        """

        @contextlib.contextmanager
        def _get_group(names):
            if len(names) == 0:
                # names = (f"Group{len(self._groups) + 1}",)
                name = "Group1"
                while pathlib.Path("nodes", name).exists():
                    name = f"Group{int(name[5:]) + 1}"
                names = (name,)

            nwd = pathlib.Path("nodes", *names)
            if any(x.nwd == nwd for x in self._groups):
                raise ValueError(f"Group {names} already exists.")

            nwd.mkdir(parents=True, exist_ok=True)

            existing_nodes = self.graph.get_sorted_nodes()

            group = NodeGroup(nwd=nwd, nodes=[])

            try:
                yield group
            finally:
                for node_uuid in self.graph.get_sorted_nodes():
                    node: Node = self.graph.nodes[node_uuid]["value"]
                    if node_uuid not in existing_nodes:
                        node.__dict__["nwd"] = group.nwd / node.name
                        node.name = f"{'_'.join(names)}_{node.name}"
                        group.nodes.append(node)
                self._groups.append(group)

        if get_graph() is not empty:
            with _get_group(names) as group:
                yield group
        else:
            with self:
                with _get_group(names) as group:
                    yield group

    def run(
        self,
        eager=False,
        repro: bool = True,
        optional: dict = None,
        save: bool = True,
        environment: dict = None,
        nodes: list = None,
    ):
        """Run the Project Graph.

        Parameters
        ----------
        eager : bool, default = False
            if True, run the nodes in eager mode.
            if False, run the nodes using dvc.
        save : bool, default = True
            if using 'eager=True' this will save the results to disk.
            Otherwise, the results will only be in memory.
        repro : bool, default = True
            if True, run dvc repro after running the nodes.
        optional : dict, default = None
            A dictionary of optional arguments for each node.
            Use {node_name: {arg_name: arg_value}} to pass arguments to nodes.
            Possible arg_names are e.g. 'always_changed: True'
        environment : dict, default = None
            A dictionary of environment variables for all nodes.
        nodes : list, default = None
            A list of node names to run. If None, run all nodes.
        """
        if not save and not eager:
            raise ValueError("Save can only be false if eager is True")

        self._handle_environment(environment)

        if optional is None:
            optional = {}

        node_names = None
        if nodes is not None:
            node_names = []
            for node in nodes:
                if isinstance(node, str):
                    node_names.append(node)
                elif isinstance(node, Node):
                    node_names.append(node.name)
                elif isinstance(node, NodeGroup):
                    node_names.extend([x.name for x in node.nodes])
                else:
                    raise ValueError(f"Unknown node type {type(node)}")

        for node_uuid in self.graph.get_sorted_nodes():
            node: Node = self.graph.nodes[node_uuid]["value"]
            if node_names is not None and node.name not in node_names:
                continue
            if node._external_:
                continue
            if eager:
                # update connectors
                log.info(f"Running node {node}")
                self.graph._update_node_attributes(node, UpdateConnectors())
                node.run()
                if save:
                    node.save()
                node.state.loaded = True
            else:
                log.info(f"Adding node {node}")
                cmd = get_dvc_cmd(
                    node, git_only_repo=self.git_only_repo, **optional.get(node.name, {})
                )
                for x in cmd:
                    run_dvc_cmd(x)
                node.save(results=False)
        if not eager and repro:
            self.repro()
            # TODO should we load the nodes here? Maybe, if lazy loading is implemented.

    def build(
        self, environment: dict = None, optional: dict = None, nodes: list = None
    ) -> None:
        """Build the project graph without running it."""
        self.run(repro=False, environment=environment, optional=optional, nodes=nodes)

    def repro(self) -> None:
        """Run dvc repro."""
        run_dvc_cmd(["repro"])
        # TODO load nodes afterwards!

    def _handle_environment(self, environment: dict):
        """Write global environment variables to the env.yaml file."""
        if environment is not None:
            file = pathlib.Path("env.yaml")
            try:
                context = yaml.safe_load(file.read_text())
            except FileNotFoundError:
                context = {}

            context["global"] = environment
            file.write_text(yaml.safe_dump(context))

    def load(self):
        """Load all nodes in the project."""
        for node_uuid in self.graph.get_sorted_nodes():
            node = self.graph.nodes[node_uuid]["value"]
            node.load()

    def get_nodes(self) -> dict[str, znflow.Node]:
        """Get the nodes in the project."""
        nodes = {}
        for node_uuid in self.graph.get_sorted_nodes():
            node = self.graph.nodes[node_uuid]["value"]
            nodes[node.name] = node
        return nodes

    def remove(self, name):
        """Remove all nodes with the given name from the project."""
        # TODO there should never be multiple nodes with the same name
        for node_uuid in self.graph.get_sorted_nodes():
            node = self.graph.nodes[node_uuid]["value"]
            if node.name == name:
                self.graph.remove_node(node_uuid)

    @property
    def nodes(self) -> dict[str, znflow.Node]:
        """Get the nodes in the project."""
        return self.get_nodes()

    def create_branch(self, name: str) -> "Branch":
        """Create a branch in the project."""
        branch = Branch(self, name)
        branch.create()
        return branch

    @contextlib.contextmanager
    def create_experiment(self, name: str = None, queue: bool = True) -> Experiment:
        """Create a new experiment."""
        # TODO: return an experiment object that allows you to load the results
        # TODO this context manager WILL NOT ADD new nodes to the graph.

        exp = Experiment(name, project=self)

        repo = git.Repo()
        dirty = repo.is_dirty()
        if dirty:
            repo.git.stash("save", "--include-untracked")

        force = self.force
        self.force = True
        with self:
            yield exp
        self.run(repro=False)  # save nodes and update dvc.yaml
        self.force = force

        cmd = ["dvc", "exp", "run"]
        if queue:
            cmd.append("--queue")
        if name is not None:
            cmd.extend(["--name", name])
        try:
            proc = subprocess.run(cmd, capture_output=True, check=True)
            # "Reproducing", "Experiment", "'exp-name'"
            exp.name = proc.stdout.decode("utf-8").split()[2].replace("'", "")
        finally:
            repo.git.reset("--hard")
            repo.git.clean("-fd")
            if dirty:
                repo.git.stash("pop")
        if not queue:
            exp.apply()

    @property
    def experiments(self, *args, **kwargs) -> dict[str, Experiment]:
        """List all experiments."""
        experiments = dvc.api.exp_show(*args, **kwargs)
        return {
            experiment["Experiment"]: Experiment(experiment["rev"], project=self)
            for experiment in experiments
            if experiment["Experiment"] is not None
        }

    def run_exp(self, jobs: int = 1) -> None:
        """Run all queued experiments."""
        run_dvc_cmd(["exp", "run", "--run-all", "--jobs", str(jobs)])

    @property
    def branches(self):
        """Get the branches in the project."""
        repo = git.Repo()  # todo should be self.repo
        return [Branch(project=self, name=branch.name) for branch in repo.branches]


@dataclasses.dataclass
class Experiment:
    """A DVC Experiment."""

    name: str
    project: Project
    # TODO the project can not be used. The graph could be different.
    #  Project must be loaded from rev.
    # TODO name / rev / remote ...

    nodes: dict = dataclasses.field(default_factory=dict, init=False, repr=False)

    def apply(self) -> None:
        """Apply the experiment."""
        run_dvc_cmd(["exp", "apply", self.name])

    def load(self) -> None:
        """Load the nodes from this experiment."""
        self.nodes = {
            name: node.from_rev(name=name, rev=self.name)
            for name, node in self.project.get_nodes().items()
        }

    def __getitem__(self, key: typing.Union[str, Node]) -> Node:
        """Get the Node from the experiment."""
        if len(self.nodes) == 0:
            self.load()
        if isinstance(key, Node):
            key = key.name
        return self.nodes[key]


@dataclasses.dataclass
class Branch:
    """The ZnTrack Branch class for managing experiments."""

    project: Project
    name: str
    repo: git.Repo = dataclasses.field(init=False, repr=False, default_factory=git.Repo)

    def create(self):
        """Create the branch."""
        self.repo.create_head(self.name)

    def queue(self, name: str):
        """Queue the branch to run."""
        active_branch = self.repo.active_branch
        self.repo.git.checkout(self.name)
        self.run(eager=False, repro=False)

        # if self.repo.is_dirty():
        # if len(self.repo.untracked_files) > 0:
        self.repo.git.add(A=True)
        self.repo.index.commit(f"parameters for {name}")
        run_dvc_cmd(["exp", "run", "--name", name, "--queue"])

        for node_uuid in self.graph.get_sorted_nodes():
            node = self.graph.nodes[node_uuid]["value"]
            node.state.rev = name
        active_branch.checkout()


@dataclasses.dataclass
class NodeGroup:
    """A group of nodes."""

    nwd: pathlib.Path
    nodes: list[Node]

    def __contains__(self, item: Node) -> bool:
        """Check if the Node is in the group."""
        return item in self.nodes

    def __len__(self) -> int:
        """Get the number of nodes in the group."""
        return len(self.nodes)
