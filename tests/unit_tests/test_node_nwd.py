import pathlib

import zntrack


class MyNode(zntrack.Node):
    def run(self):
        pass


def test_node_nwd(proj_path):
    with zntrack.Project():
        n = MyNode()

    assert n.nwd == pathlib.Path("nodes", "MyNode")


def test_no_node_name(proj_path):
    assert zntrack.Node().nwd == pathlib.Path("nodes", "Node")

    # it has to be given explicitly
    n = zntrack.Node(name="SomeNode")
    assert n.nwd == pathlib.Path("nodes", "SomeNode")
