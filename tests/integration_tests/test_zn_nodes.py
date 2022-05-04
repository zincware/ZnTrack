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


def test_ExampleNodeWithDefaults(proj_path):
    with pytest.raises(ValueError):
        # zn.Nodes does not support default values because they can be mutable
        _ = zn.Nodes(NodeViaParams())
