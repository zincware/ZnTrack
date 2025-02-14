import datetime
import unittest.mock as mock

from znflow.deployment import VanillaDeployment


class ZnTrackDeployment(VanillaDeployment):
    def _run_node(self, node_uuid):
        node = self.graph.nodes[node_uuid]["value"]
        start_time = datetime.datetime.now()
        node.state.increment_run_count()
        node.state.save_node_meta()
        if hasattr(node, "_method"):
            method_string = getattr(node, "_method")
            method = getattr(node, method_string)
            if method != "run":
                # mock the node.run with the method
                with mock.patch.object(node, "run", method):
                    # TODO: this needs to be fixed on the znflow side!
                    super()._run_node(node_uuid)
            else:
                super()._run_node(node_uuid)
        else:
            super()._run_node(node_uuid)

        run_time = datetime.datetime.now() - start_time
        node.state.add_run_time(run_time)
        node.state.save_node_meta()
        node.save()

    # TODO: when finished all Nodes, commit all changes
