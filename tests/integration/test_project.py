import pytest

import zntrack


class WriteIO(zntrack.Node):
    inputs = zntrack.zn.params()
    outputs = zntrack.zn.outs()

    def run(self) -> None:
        self.outputs = self.inputs


@pytest.mark.parametrize("assert_before_exp", [True, False])
def test_WriteIO(tmp_path_2, assert_before_exp):
    """Test the WriteIO node."""
    with zntrack.Project() as project:
        node = WriteIO(inputs="Hello World")

    project.run()
    node.load()
    if assert_before_exp:
        assert node.outputs == "Hello World"

    with project.create_experiment(name="exp1") as exp1:
        node.inputs = "Hello World"

    with project.create_experiment(name="exp2") as exp2:
        node.inputs = "Lorem Ipsum"

    assert exp1.name == "exp1"
    assert exp2.name == "exp2"

    project.run_exp()
    assert node.from_rev(rev="exp1").inputs == "Hello World"
    assert node.from_rev(rev="exp1").outputs == "Hello World"

    assert node.from_rev(rev="exp2").inputs == "Lorem Ipsum"
    assert node.from_rev(rev="exp2").outputs == "Lorem Ipsum"


@pytest.mark.parametrize("assert_before_exp", [True, False])
def test_WriteIO_no_name(tmp_path_2, assert_before_exp):
    """Test the WriteIO node."""
    with zntrack.Project() as project:
        node = WriteIO(inputs="Hello World")

    project.run()
    node.load()
    if assert_before_exp:
        assert node.outputs == "Hello World"

    with project.create_experiment() as exp1:
        node.inputs = "Hello World"

    with project.create_experiment() as exp2:
        node.inputs = "Lorem Ipsum"

    project.run_exp()

    exp1.load()
    assert exp1.nodes["WriteIO"].inputs == "Hello World"
    assert exp1.nodes["WriteIO"].outputs == "Hello World"

    assert exp1["WriteIO"].inputs == "Hello World"
    assert exp1["WriteIO"].outputs == "Hello World"

    exp2.load()
    assert exp2.nodes["WriteIO"].inputs == "Lorem Ipsum"
    assert exp2.nodes["WriteIO"].outputs == "Lorem Ipsum"

    assert exp2["WriteIO"].inputs == "Lorem Ipsum"
    assert exp2["WriteIO"].outputs == "Lorem Ipsum"


def test_project_remove_graph(proj_path):
    with zntrack.Project() as project:
        node = WriteIO(inputs="Hello World")
    project.run()
    node.load()
    assert node.outputs == "Hello World"

    with zntrack.Project(remove_existing_graph=True) as project:
        node2 = WriteIO(inputs="Lorem Ipsum", name="node2")
    project.run()
    node2.load()
    assert node2.outputs == "Lorem Ipsum"
    with pytest.raises(zntrack.exceptions.NodeNotAvailableError):
        node.load()


def test_project_repr_node(tmp_path_2):
    with zntrack.Project() as project:
        node = WriteIO(inputs="Hello World")
        print(node)


def test_automatic_node_names_False(tmp_path_2):
    with pytest.raises(zntrack.exceptions.DuplicateNodeNameError):
        with zntrack.Project(automatic_node_names=False) as project:
            _ = WriteIO(inputs="Hello World")
            _ = WriteIO(inputs="Lorem Ipsum")


def test_automatic_node_names_True(tmp_path_2):
    with zntrack.Project(automatic_node_names=True) as project:
        node = WriteIO(inputs="Hello World")
        node2 = WriteIO(inputs="Lorem Ipsum")

    assert node.name == "WriteIO"
    assert node2.name == "WriteIO_1"

    project.run()
    project.load()
    assert "WriteIO" in project.nodes
    assert "WriteIO_1" in project.nodes

    assert node.outputs == "Hello World"
    assert node2.outputs == "Lorem Ipsum"
