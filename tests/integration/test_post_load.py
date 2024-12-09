import zntrack


class NodeWithPostLoad(zntrack.Node):
    params: float = zntrack.params()
    outs: float = zntrack.outs()

    def _post_load_(self):
        self.params += 1

    def run(self):
        self.outs = self.params


def test_post_load(proj_path):
    project = zntrack.Project()
    with project:
        node = NodeWithPostLoad(params=1)

    assert node.params == 1
    project.repro()

    n = node.from_rev()
    assert n.params == 2 # modified by _post_load_
    assert n.outs == 1