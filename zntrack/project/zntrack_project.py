"""The class for the ZnTrackProject."""
from __future__ import annotations

import contextlib
import dataclasses
import json
import logging
import pathlib

import git
import yaml
import znflow
from znflow.graph import _UpdateConnectors

from zntrack.core.node import Node, get_dvc_cmd
from zntrack.utils import capture_run_dvc_cmd, run_dvc_cmd

log = logging.getLogger(__name__)


class _ProjectBase(znflow.DiGraph):
    def run(
        self, eager=False, repro: bool = True, optional: dict = None, save: bool = True
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
        """
        if not save and not eager:
            raise ValueError("Save can only be false if eager is True")
        if optional is None:
            optional = {}
        for node_uuid in self.get_sorted_nodes():
            node: Node = self.nodes[node_uuid]["value"]
            if eager:
                # update connectors
                log.info(f"Running node {node}")
                self._update_node_attributes(node, _UpdateConnectors())
                node.run()
                if save:
                    node.save()
                node.state.loaded = True
            else:
                log.info(f"Adding node {node}")
                cmd = get_dvc_cmd(node, **optional.get(node.name, {}))
                for x in cmd:
                    run_dvc_cmd(x)
                node.save(results=False)
        if not eager and repro:
            run_dvc_cmd(["repro"])
            # TODO should we load the nodes here? Maybe, if lazy loading is implemented.

    def load(self):
        for node_uuid in self.get_sorted_nodes():
            node = self.nodes[node_uuid]["value"]
            node.load()

    def get_nodes(self) -> dict[str, znflow.Node]:
        nodes = {}
        for node_uuid in self.get_sorted_nodes():
            node = self.nodes[node_uuid]["value"]
            nodes[node.name] = node
        return nodes


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


class Project(_ProjectBase):
    """The ZnTrack Project class."""

    def __init__(self, initialize: bool = True) -> None:
        """Initialize the Project.

        Attributes
        ----------
        initialize : bool, default = True
            If True, initialize a git repository and a dvc repository.
        """
        # TODO maybe it is not a good idea to base everything on the DiGraph class.
        #  It seems to call some class methods
        super().__init__()
        if initialize:
            _initalize()

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

        yield exp

        for node_uuid in self.get_sorted_nodes():
            node: Node = self.nodes[node_uuid]["value"]
            node.save(results=False)

        cmd = ["exp", "run"]
        if queue:
            cmd.append("--queue")
        if name is not None:
            cmd.extend(["--name", name])
        exp.name = capture_run_dvc_cmd(cmd).split("'")[1]

    def run_exp(self) -> None:
        """Run all queued experiments."""
        run_dvc_cmd(["exp", "run", "--run-all"])

    @property
    def branches(self):
        """Get the branches in the project."""
        repo = git.Repo()
        return [Branch(project=self, name=branch.name) for branch in repo.branches]


@dataclasses.dataclass
class Experiment:
    """A DVC Experiment."""

    name: str
    project: Project

    nodes: dict = dataclasses.field(default_factory=dict, init=False, repr=False)

    def load(self) -> None:
        """Load the nodes from this experiment."""
        self.nodes = {
            name: node.from_rev(name=name, rev=self.name)
            for name, node in self.project.get_nodes().items()
        }


class Branch(_ProjectBase):
    """The ZnTrack Branch class for managing experiments."""

    def __init__(self, project=None, name=None) -> None:
        """Initialize a Branch."""
        super().__init__()
        self.project = project
        self.name = name
        self.repo = git.Repo()

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

        for node_uuid in self.get_sorted_nodes():
            node = self.nodes[node_uuid]["value"]
            node.state.rev = name
        active_branch.checkout()
