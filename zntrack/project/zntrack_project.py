"""The class for the ZnTrackProject."""
import logging

import dvc.cli
import znflow
from znflow.graph import _UpdateConnectors

from zntrack.core.node import get_dvc_cmd

log = logging.getLogger(__name__)


class Project(znflow.DiGraph):
    """The ZnTrack Project class."""

    def __init__(self, eager=False, repro: bool = True):
        """The Project Constructor.

        Parameters
        ----------
        eager : bool, default = False
            if True, run the nodes in eager mode.
            if False, run the nodes using dvc.
        repro : bool, default = True
            if True, run dvc repro after running the nodes.
        """
        super().__init__()
        self.eager = eager
        self.repro = repro

    def run(self):
        """Run the Project Graph."""
        for node_uuid in self.get_sorted_nodes():
            node = self.nodes[node_uuid]["value"]
            if self.eager:
                # update connectors
                self._update_node_attributes(node, _UpdateConnectors())
                node.run()
                node.save()
            else:
                cmd = get_dvc_cmd(node)
                node.save()
                dvc.cli.main(cmd)
        if not self.eager and self.repro:
            dvc.cli.main(["repro"])
