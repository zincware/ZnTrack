import pytest

from zntrack import Node, Project, zn


class NodeViaParams(Node):
    param1 = zn.params()

    def run(self):
        raise NotImplementedError


class ExampleNode(Node):
    params1: NodeViaParams = zn.nodes()
    params2: NodeViaParams = zn.nodes()

    outs = zn.outs()

    def run(self):
        self.outs = self.params1.param1 + self.params2.param1


@pytest.mark.parametrize("eager", [True, False])
def test_ExampleNode(proj_path, eager):
    project = Project()
    parameter_1 = NodeViaParams(param1=1)
    parameter_2 = NodeViaParams(param1=10)

    with project:
        node = ExampleNode(params1=parameter_1, params2=parameter_2)

    project.run(eager=eager)
    if not eager:
        node.load()
    assert node.params1.param1 == 1
    assert node.params2.param1 == 10
    assert node.outs == 11

    if not eager:
        # Check new instance also works
        node = node.from_rev()
        assert node.params1.param1 == 1
        assert node.params2.param1 == 10
        assert node.outs == 11
