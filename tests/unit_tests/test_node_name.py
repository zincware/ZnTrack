import zntrack


class MyNode(zntrack.Node):
    pass


def test_node_name(proj_path):
    with zntrack.Project():
        n = MyNode()

    assert n.name == "MyNode"


def test_duplicate_node_name(proj_path):
    with zntrack.Project():
        n1 = MyNode()
        n2 = MyNode()
        n3 = MyNode()
        n4 = MyNode()

    assert n1.name == "MyNode"
    assert n2.name == "MyNode_1"
    assert n3.name == "MyNode_2"
    assert n4.name == "MyNode_3"
