import pathlib

import pytest

import zntrack


class MyNode(zntrack.Node):
    def run(self):
        pass


def test_node_nwd(proj_path):
    with zntrack.Project():
        n = MyNode()

    assert n.nwd == pathlib.Path("nodes", "MyNode")


def test_no_node_name(proj_path):
    # if the node was not created inside a graph context, it will not have an assigned name
    with pytest.raises(ValueError, match="Unable to determine node name."):
        zntrack.Node().nwd

    # it has to be given explicitly
    n = zntrack.Node(name="SomeNode")
    assert n.nwd == pathlib.Path("nodes", "SomeNode")
