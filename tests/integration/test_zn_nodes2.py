import shutil

import pytest

import zntrack
from zntrack import Node, Project, zn


class NodeViaParams(Node):
    param1 = zn.params()
    outs = zn.outs()

    def run(self):
        raise NotImplementedError


class ExampleNode(Node):
    params1: NodeViaParams = zntrack.deps()
    params2: NodeViaParams = zntrack.deps()

    outs = zn.outs()

    def run(self):
        self.outs = self.params1.param1 + self.params2.param1


class ExampleNodeLst(Node):
    params: list = zntrack.deps()
    outs = zn.outs()

    def run(self):
        self.outs = sum(p.param1 for p in self.params)


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

    assert node.params1.name == "ExampleNode+params1"
    assert node.params2.name == "ExampleNode+params2"

    if not eager:
        # Check new instance also works
        node = node.from_rev()
        assert node.params1.param1 == 1
        assert node.params2.param1 == 10
        assert node.outs == 11

        assert node.params1.name == "ExampleNode+params1"
        assert node.params2.name == "ExampleNode+params2"


@pytest.mark.parametrize("git_only_repo", [True, False])
@pytest.mark.parametrize("eager", [True, False])
def test_ExampleNodeLst(proj_path, eager, git_only_repo):
    project = Project(git_only_repo=git_only_repo)
    parameter_1 = NodeViaParams(param1=1)
    parameter_2 = NodeViaParams(param1=10)

    with project:
        node = ExampleNodeLst(params=[parameter_1, parameter_2])

    project.run(eager=eager)
    if not eager:
        node.load()
    assert node.params[0].param1 == 1
    assert node.params[1].param1 == 10
    assert node.outs == 11

    assert node.params[0].name == "ExampleNodeLst+params+0"
    assert node.params[1].name == "ExampleNodeLst+params+1"

    if not eager:
        # Check new instance also works
        nodex = node.from_rev()
        assert nodex.params[0].param1 == 1
        assert nodex.params[1].param1 == 10
        assert nodex.outs == 11
        assert nodex.params[0].name == "ExampleNodeLst+params+0"
        assert nodex.params[1].name == "ExampleNodeLst+params+1"

    parameter_1.param1 = 2  # Change parameter
    assert isinstance(parameter_1, NodeViaParams)
    with project:
        # #     # node = ExampleNodeLst(params=[parameter_1, parameter_2])
        node.params = [parameter_1, parameter_2]
    project.run(eager=eager)

    if not eager:
        node.load()
    assert node.params[0].param1 == 2
    assert node.params[1].param1 == 10
    assert node.outs == 12

    if not eager:
        # Check new instance also works
        node = node.from_rev()
        assert node.params[0].param1 == 2
        assert node.params[1].param1 == 10
        assert node.outs == 12


class RandomNumberGen(Node):
    def get_rnd(self):
        import random

        random.seed(42)

        return random.random()


class ExampleNodeWithRandomNumberGen(Node):
    rnd: RandomNumberGen = zntrack.deps()

    outs = zn.outs()

    def run(self):
        self.outs = self.rnd.get_rnd()


def test_znodes_with_random_number_gen(proj_path):
    project = Project(force=True)

    rnd = RandomNumberGen()

    with project:
        node = ExampleNodeWithRandomNumberGen(rnd=rnd)
    project.run()
    node.load(lazy=False)
    shutil.rmtree("nodes")

    project.run()

    node2 = node.from_rev()
    assert node.outs == node2.outs
