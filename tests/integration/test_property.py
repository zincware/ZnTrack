import functools

import zntrack.examples


class NodeWithProperty(zntrack.Node):
    params: int = zntrack.params(42)
    outs: dict = zntrack.outs()

    def run(self):
        self.outs = {"outs": self.params}

    @functools.cached_property
    def value(self):
        self.property_triggered = True
        return self.outs


def test_property_access_graph_building(proj_path):
    project = zntrack.Project()

    with project:
        node = NodeWithProperty()
        zntrack.examples.DepsToMetrics(deps=node.value)

    project.build()

    assert not hasattr(node, "property_triggered")

    project.repro()

    assert not hasattr(node, "property_triggered")

    # assert node.outs != -5

    with project:
        node = NodeWithProperty()
        zntrack.examples.DepsToMetrics(deps=node.value)

    assert not hasattr(node, "property_triggered")
    project.build()
    assert not hasattr(node, "property_triggered")

    # sanity check
    node.value  # trigger property access
    assert node.property_triggered is True
