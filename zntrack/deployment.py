from znflow.deployment import VanillaDeployment

class ZnTrackDeployment(VanillaDeployment):
    
    def _run_node(self, node_uuid):
        super()._run_node(node_uuid)
        node = self.graph.nodes[node_uuid]["value"]
        node.save()
