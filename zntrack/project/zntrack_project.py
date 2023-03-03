"""The class for the ZnTrackProject."""
import logging

import dvc.cli
import znflow
from znflow.graph import _UpdateConnectors

from zntrack.core.node import get_dvc_cmd

log = logging.getLogger(__name__)


class Project(znflow.DiGraph):
    """The ZnTrack Project class."""

    def __init__(self) -> None:
        """Initialize the Project.
        
        Do not allow kwargs.
        """
        super().__init__()

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
                self._update_node_attributes(node, _UpdateConnectors())
                node.run()
                node.save()
                node.state.loaded = True
            else:
                cmd = get_dvc_cmd(node)
                node.save()
                dvc.cli.main(cmd)
        if not eager and repro:
            dvc.cli.main(["repro"])
