import unittest.mock as mock

from znflow.deployment import VanillaDeployment


class ZnTrackDeployment(VanillaDeployment):
    def _run_node(self, node_uuid):
        node = self.graph.nodes[node_uuid]["value"]
        node.increment_run_count()
        if hasattr(node, "_method"):
            method_string = getattr(node, "_method")
            method = getattr(node, method_string)
            if method != "run":
                # moch the node.run with the method
                with mock.patch.object(node, "run", method):
                    # TODO: this needs to be fixed on the znflow side!
                    super()._run_node(node_uuid)
            else:
                super()._run_node(node_uuid)
        else:
            super()._run_node(node_uuid)

        node.save()

    # TODO: when finished all Nodes, commit all changes
