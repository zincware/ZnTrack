import zntrack


class NodeWithPostLoad(zntrack.Node):
    params: float = zntrack.params()
    outs: float = zntrack.outs()

    def _post_load_(self):
        self.params += 1

    def run(self):
        self.outs = self.params


class DepsOnPostLoadNode(zntrack.Node):
    deps: float = zntrack.deps()
    outs: float = zntrack.outs()

    def run(self):
        self.outs = self.deps


def test_post_load(proj_path):
    project = zntrack.Project()
    with project:
        node = NodeWithPostLoad(params=1)

    assert node.params == 1
    project.repro()

    n = node.from_rev()
    assert n.params == 2  # modified by _post_load_
    assert n.outs == 1


def test_post_load_deps(proj_path):
    project = zntrack.Project()

    with project:
        node = NodeWithPostLoad(params=1)
        dep_node = DepsOnPostLoadNode(deps=node.outs)
        dep_node_2 = DepsOnPostLoadNode(deps=node.params)

    project.repro()

    # post load has not been called
    assert dep_node.outs == 1
    assert node.outs == 1
    assert node.params == 1
    # assert dep_node_2.deps == 2 # has not been resolved from a connection
    assert dep_node_2.outs == 2

    # post load has been called
    n = dep_node.from_rev()
    assert n.outs == 1
    assert n.deps == 1

    # _post_load_ will also be called if the node is resolved from a connection
    n2 = dep_node_2.from_rev(name=dep_node_2.name)
    assert n2.outs == 2
    assert n2.deps == 2

    assert node.from_rev().outs == 1
    assert node.from_rev().params == 2
