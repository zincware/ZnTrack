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
from znflow.handler import UpdateConnectors

from zntrack import exceptions
from zntrack.core.node import Node, get_dvc_cmd
from zntrack.utils import NodeName, config, run_dvc_cmd

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
        config.files.zntrack.write_text(json.dumps({}))
        config.files.dvc.write_text(yaml.safe_dump({}))
        config.files.params.write_text(yaml.safe_dump({}))
        repo.git.add(A=True)
        repo.index.commit("Project initialized.")


class ZnTrackGraph(znflow.DiGraph):
    """Subclass of the znflow.DiGraph."""

    project: Project = None

    def add_node(self, node_for_adding: Node, **attr):
        """Rename Nodes if required."""
        node_for_adding.name = NodeName(self.active_group, node_for_adding.name)

        super().add_node(node_for_adding, **attr)


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

    graph: ZnTrackGraph = dataclasses.field(default_factory=ZnTrackGraph, init=False)
    initialize: bool = True
    remove_existing_graph: bool = False
    automatic_node_names: bool = False
    git_only_repo: bool = True
    force: bool = False

    _groups: dict[str, NodeGroup] = dataclasses.field(
        default_factory=dict, init=False, repr=False
    )

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
            config.files.zntrack.unlink(missing_ok=True)
            config.files.dvc.unlink(missing_ok=True)
            config.files.params.unlink(missing_ok=True)
            shutil.rmtree("nodes", ignore_errors=True)

    def __enter__(self, *args, **kwargs):
        """Enter the graph context."""
        self.graph.__enter__(*args, **kwargs)
        return self

    def __exit__(self, *args, **kwargs):
        """Exit the graph context."""
        self.graph.__exit__(*args, **kwargs)

        node_names = []
        for node_uuid in self.graph.nodes:
            node = self.graph.nodes[node_uuid]["value"]
            if node._external_:
                continue

            if node.name in node_names and not self.force:
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
        if not names:
            name = "Group1"
            while pathlib.Path("nodes", name).exists():
                name = f"Group{int(name[5:]) + 1}"
            names = (name,)

        try:
            grp = self._groups[names]
        except KeyError:
            nwd = pathlib.Path("nodes", *names)
            nwd.mkdir(parents=True, exist_ok=True)
            grp = NodeGroup(name="_".join(names), nwd=nwd, nodes=[])
            self._groups[names] = grp

        with self.graph.group(names):
            yield grp
        # TODO: do we even need the group object?
        grp.nodes = [self.graph.nodes[x]["value"] for x in self.graph.get_group(names)]

        # we update the nwd when closing the context manager
        # changing the name is no longer possible after this
        for node in grp.nodes:
            node.__dict__["nwd"] = grp.nwd / node._name_.get_name_without_groups()

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

    name: tuple[str]
    nwd: pathlib.Path
    nodes: list[Node]

    def __contains__(self, item: Node) -> bool:
        """Check if the Node is in the group."""
        return item in self.nodes

    def __len__(self) -> int:
        """Get the number of nodes in the group."""
        return len(self.nodes)
