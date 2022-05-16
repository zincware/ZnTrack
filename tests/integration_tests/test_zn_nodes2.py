import os
import shutil
import subprocess

import pytest

from zntrack import zn
from zntrack.core.base import Node


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class NodeViaParams(Node):
    _hash = zn.Hash()
    param1 = zn.params()
    param2 = zn.params()

    def run(self):
        pass


class ExampleNode(Node):
    params1: NodeViaParams = zn.Nodes()
    params2: NodeViaParams = zn.Nodes()

    outs = zn.outs()

    def run(self):
        self.outs = self.params1.param1 + self.params2.param2


def test_ExampleNode(proj_path):
    ExampleNode(
        params1=NodeViaParams(param1="Hello", param2="World"),
        params2=NodeViaParams(param1="Lorem", param2="Ipsum"),
    ).write_graph(run=True)

    example_node = ExampleNode.load()

    assert example_node.params1.param1 == "Hello"
    assert example_node.params1.param2 == "World"
    assert example_node.params2.param1 == "Lorem"
    assert example_node.params2.param2 == "Ipsum"
    assert example_node.outs == "HelloIpsum"


class SingleExampleNode(Node):
    params1 = zn.Nodes()
    outs = zn.outs()

    def run(self):
        self.outs = "Lorem Ipsum"


def test_SingleExampleNode(proj_path):
    SingleExampleNode().write_graph(run=True)

    assert SingleExampleNode.load().outs == "Lorem Ipsum"


class NodeNodeParams(Node):
    deps: NodeViaParams = zn.deps()
    node: NodeViaParams = zn.Nodes()
    _hash = zn.Hash()

    def run(self):
        pass


class ExampleNode2(Node):
    params1: NodeNodeParams = zn.Nodes()
    params2 = zn.Nodes()

    def run(self):
        pass


def test_depth_graph(proj_path):
    node_1 = NodeViaParams(param1="Lorem", param2="Ipsum", name="Node1")
    node_1.write_graph(run=True)  # defined as dependency, so it must run first.

    node_2 = NodeViaParams(param1="Lorem", param2="Ipsum")

    node_3 = NodeNodeParams(deps=node_1, node=node_2, name="Node3")

    node_4 = ExampleNode2(params1=node_3)

    node_4.write_graph(run=True)

    node_4 = ExampleNode2.load()

    assert node_4.params1.deps.param1 == "Lorem"
    assert node_4.params1.node.param2 == "Ipsum"

    assert node_4.params1.node_name == "ExampleNode2-params1"
    assert node_4.params1.deps.node_name == "Node1"
    assert node_4.params1.node.node_name == "ExampleNode2-params1-node"


class NodeWithOuts(Node):
    input = zn.params()
    factor = zn.params()
    output = zn.outs()
    _hash = zn.Hash()

    def run(self):
        self.output = self.input * self.factor


def test_NodeWithOuts(proj_path):
    node_1 = SingleExampleNode(params1=NodeWithOuts(factor=2))
    node_1.write_graph(run=True)

    assert SingleExampleNode.load().params1.factor == 2
