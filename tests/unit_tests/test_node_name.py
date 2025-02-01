import pytest

import zntrack


class MyNode(zntrack.Node):
    pass


# Basic Naming Tests
def test_default_node_name(proj_path):
    """Test that a node gets the correct default name"""
    with zntrack.Project():
        node = MyNode()
        assert node.name == "MyNode"


def test_custom_node_name(proj_path):
    """Test that a node gets a custom name when specified"""
    with zntrack.Project():
        node = MyNode(name="CustomName")
        assert node.name == "CustomName"


# Duplicate Naming Tests
def test_unique_default_node_names(proj_path):
    """Test that multiple unnamed nodes receive unique names"""
    with zntrack.Project():
        n1 = MyNode()
        n2 = MyNode()
        n3 = MyNode()
        n4 = MyNode()

        assert n1.name == "MyNode"
        assert n2.name == "MyNode_1"
        assert n3.name == "MyNode_2"
        assert n4.name == "MyNode_3"


def test_duplicate_named_node_error(proj_path):
    """Test that an explicitly named node cannot be duplicated"""
    with zntrack.Project() as project:
        MyNode(name="A")

    with pytest.raises(ValueError, match="A node with the name 'A' already exists."):
        with project:
            MyNode(name="A")


# Grouped Naming Tests
def test_grouped_node_names(proj_path):
    """Test that nodes within groups get correct names"""
    project = zntrack.Project()

    with project:
        n1 = MyNode()
        n2 = MyNode()
        named_node = MyNode(name="SomeNode")

        assert n1.name == "MyNode"
        assert n2.name == "MyNode_1"
        assert named_node.name == "SomeNode"

    with project.group("grp1"):
        n3 = MyNode()
        n4 = MyNode()

        assert n3.name == "grp1_MyNode"
        assert n4.name == "grp1_MyNode_1"


def test_nested_grouped_node_names(proj_path):
    """Test that nested group names are correctly prefixed"""
    project = zntrack.Project()

    with project.group("A", "B"):
        n1 = MyNode()
        n2 = MyNode()

        assert n1.name == "A_B_MyNode"
        assert n2.name == "A_B_MyNode_1"


# Grouped Custom Name Tests
def test_grouped_custom_node_names(proj_path):
    """Test that nodes with custom names within groups get correctly prefixed"""
    project = zntrack.Project()

    with project.group("grp1"):
        n1 = MyNode(name="Alpha")
        n2 = MyNode(name="Beta")

        assert n1.name == "grp1_Alpha"
        assert n2.name == "grp1_Beta"

    project.build()

    assert n1.name == "grp1_Alpha"
    assert n2.name == "grp1_Beta"


def test_nested_grouped_custom_node_names(proj_path):
    """Test that nodes with custom names within nested groups get correctly prefixed"""
    project = zntrack.Project()

    with project.group("A", "B"):
        n1 = MyNode(name="Alpha")
        n2 = MyNode(name="Beta")

        assert n1.name == "A_B_Alpha"
        assert n2.name == "A_B_Beta"

    project.build()

    assert n1.name == "A_B_Alpha"
    assert n2.name == "A_B_Beta"
    assert n1.name == "A_B_Alpha"
    assert n2.name == "A_B_Beta"


# Grouped Duplicate Naming Tests
def test_grouped_duplicate_named_node(proj_path):
    """Test that nodes with the same custom name in different groups are unique"""
    project = zntrack.Project()

    with project.group("grp1"):
        n1 = MyNode(name="A")
        assert n1.name == "grp1_A"

    with project.group("grp2"):
        n2 = MyNode(name="A")
        assert n2.name == "grp2_A"

    project.build()

    assert n1.name == "grp1_A"
    assert n2.name == "grp2_A"
    assert n1.name == "grp1_A"
    assert n2.name == "grp2_A"

    with pytest.raises(ValueError, match="A node with the name 'grp1_A' already exists."):
        with project.group("grp1"):
            MyNode(name="A")
