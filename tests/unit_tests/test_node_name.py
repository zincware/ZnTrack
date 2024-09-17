import pytest

import zntrack


class MyNode(zntrack.Node):
    pass


def test_node_name(proj_path):
    with zntrack.Project():
        n = MyNode()
        assert n.name == "MyNode"

    assert n.name == "MyNode"


def test_duplicate_node_name(proj_path):
    with zntrack.Project():
        n1 = MyNode()
        assert n1.name == "MyNode"
        n2 = MyNode()
        assert n2.name == "MyNode_1"
        n3 = MyNode()
        assert n3.name == "MyNode_2"
        n4 = MyNode()
        assert n4.name == "MyNode_3"

    assert n1.name == "MyNode"
    assert n2.name == "MyNode_1"
    assert n3.name == "MyNode_2"
    assert n4.name == "MyNode_3"


def test_grouped_node_name(proj_path):
    project = zntrack.Project()

    with project:
        n1 = MyNode()
        assert n1.name == "MyNode"
        n2 = MyNode()
        assert n2.name == "MyNode_1"
        n_named = MyNode(name="SomeNode")
        assert n_named.name == "SomeNode"
        assert n_named.__dict__["name"] == "SomeNode"

    with project.group("grp1"):
        n3 = MyNode()
        assert n3.name == "grp1_MyNode"
        n4 = MyNode()
        assert n4.name == "grp1_MyNode_1"

    assert n1.name == "MyNode"
    assert n2.name == "MyNode_1"
    assert n3.name == "grp1_MyNode"
    assert n4.name == "grp1_MyNode_1"

def test_duplicate_named_node():
    with zntrack.Project() as proj:
        n1 = MyNode(name="A")
    with pytest.raises(ValueError):
        with proj:
            n2 = MyNode(name="A")
    
