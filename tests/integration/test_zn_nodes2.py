import dataclasses
import shutil
import typing as t

import pytest

import zntrack
from zntrack import Node, Project


@dataclasses.dataclass
class NodeViaParams:
    param1: t.Any = zntrack.params()


class ExampleNode(Node):
    params1: t.Any = zntrack.deps()
    params2: t.Any = zntrack.deps()

    outs: t.Any = zntrack.outs()

    def run(self):
        self.outs = self.params1 + self.params2


class ExampleNodeLst(Node):
    params: list = zntrack.deps()
    outs: int = zntrack.outs()

    def run(self):
        self.outs = sum(p for p in self.params)


@pytest.mark.xfail(reason="pending implementation")
@pytest.mark.parametrize("eager", [True, False])
def test_ExampleNode(proj_path, eager):
    project = Project()
    parameter_1 = NodeViaParams(param1=1)
    parameter_2 = NodeViaParams(param1=10)

    with project:
        node = ExampleNode(params1=parameter_1, params2=parameter_2)

    project.run(eager=eager)
    # if not eager:
    #     node.load()
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


@pytest.mark.xfail(reason="pending implementation")
@pytest.mark.parametrize("eager", [False])
def test_ExampleNodeLst(proj_path, eager):
    project = Project()
    parameter_1 = NodeViaParams(param1=1)
    parameter_2 = NodeViaParams(param1=10)

    with project:
        node = ExampleNodeLst(params=[parameter_1.param1, parameter_2.param1])

    if eager:
        project.run()
    else:
        project.repro()
    assert node.params[0] == 1
    assert node.params[1] == 10
    assert node.outs == 11

    parameter_1.param1 = 2

    with zntrack.Project() as project:
        node = ExampleNodeLst(params=[parameter_1.param1, parameter_2.param1])
        # passing a parameter of a dataclass is not possible

    if eager:
        project.run()
    else:
        project.repro()
        node = node.from_rev()
    assert node.params[0] == 2
    assert node.params[1] == 10
    assert node.outs == 12

    # assert isinstance(parameter_1, NodeViaParams)
    # with project:
    #     # #     # node = ExampleNodeLst(params=[parameter_1, parameter_2])
    #     node.params = [parameter_1, parameter_2]
    # project.run(eager=eager)

    # # if not eager:
    # #     node.load()
    # assert node.params[0].param1 == 2
    # assert node.params[1].param1 == 10
    # assert node.outs == 12

    # if not eager:
    #     # Check new instance also works
    #     node = node.from_rev()
    #     assert node.params[0].param1 == 2
    #     assert node.params[1].param1 == 10
    #     assert node.outs == 12


@dataclasses.dataclass
class RandomNumberGen:
    seed: int = 42

    def get_rnd(self):
        import random

        random.seed(self.seed)

        return random.random()


class ExampleNodeWithRandomNumberGen(Node):
    rnd: RandomNumberGen = zntrack.deps()

    outs: int = zntrack.outs()

    def run(self):
        self.outs = self.rnd.get_rnd()


def test_znodes_with_random_number_gen(proj_path):
    project = Project(force=True)

    rnd = RandomNumberGen()

    with project:
        node = ExampleNodeWithRandomNumberGen(rnd=rnd)
    project.run()
    # node.load(lazy=False)
    shutil.rmtree("nodes")

    project.run()

    node2 = node.from_rev()
    assert node.outs == node2.outs
