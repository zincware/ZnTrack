"""The class for the ZnTrackProject."""
from __future__ import annotations

import logging

import dvc.cli
import git
import znflow
from znflow.graph import _UpdateConnectors

from zntrack.core.node import get_dvc_cmd

log = logging.getLogger(__name__)


class _ProjectBase(znflow.DiGraph):
    def run(self, eager=False, repro: bool = True):
        """Run the Project Graph.

        Parameters
        ----------
        eager : bool, default = False
            if True, run the nodes in eager mode.
            if False, run the nodes using dvc.
        repro : bool, default = True
            if True, run dvc repro after running the nodes.
        """
        for node_uuid in self.get_sorted_nodes():
            node = self.nodes[node_uuid]["value"]
            if eager:
                # update connectors
                log.info(f"Running node {node}")
                self._update_node_attributes(node, _UpdateConnectors())
                node.run()
                node.save()
                node.state.loaded = True
            else:
                log.info(f"Adding node {node}")
                cmd = get_dvc_cmd(node)
                node.save()
                dvc.cli.main(cmd)
        if not eager and repro:
            dvc.cli.main(["repro"])

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


class Project(_ProjectBase):
    """The ZnTrack Project class."""

    def __init__(self) -> None:
        """Initialize the Project.

        Do not allow kwargs.
        """
        super().__init__()

        try:
            _ = git.Repo()
        except git.exc.InvalidGitRepositoryError:
            repo = git.Repo.init()
            repo.init()
            dvc.cli.main(["init", "--quiet"])
            repo.git.add(A=True)
            repo.index.commit("Project initialized.")

    def create_branch(self, name: str) -> "Branch":
        """Create a branch in the project."""
        branch = Branch(self, name)
        branch.create()
        return branch

    def run_exp(self) -> None:
        """Run all queued experiments."""
        dvc.cli.main(["exp", "run", "--run-all"])

    @property
    def branches(self):
        """Get the branches in the project."""
        repo = git.Repo()
        return [Branch(project=self, name=branch.name) for branch in repo.branches]


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
        dvc.cli.main(["exp", "run", "--name", name, "--queue"])

        for node_uuid in self.get_sorted_nodes():
            node = self.nodes[node_uuid]["value"]
            node.state.rev = name
        active_branch.checkout()
