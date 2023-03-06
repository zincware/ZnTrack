import dvc.cli
import pytest

import zntrack


class AddNumbers(zntrack.Node):
    a = zntrack.zn.params()
    b = zntrack.zn.params()
    c = zntrack.zn.outs()

    def run(self):
        self.c = self.a + self.b


class AddNodes(zntrack.Node):
    a = zntrack.zn.deps()
    b = zntrack.zn.deps()
    c = zntrack.zn.outs()

    def run(self):
        self.c = self.a.c + self.b.c


class AddNodeAttributes(zntrack.Node):
    a = zntrack.zn.deps()
    b = zntrack.zn.deps()
    c = zntrack.zn.outs()

    def run(self):
        self.c = self.a + self.b


@pytest.mark.parametrize("eager", [True, False])
def test_AddNodes(proj_path, eager):
    with zntrack.Project() as project:
        add_numbers_a = AddNumbers(a=1, b=2, name="AddNumbersA")
        add_numbers_b = AddNumbers(a=1, b=3, name="AddNumbersB")
        add_nodes = AddNodes(a=add_numbers_a, b=add_numbers_b)

    assert not add_numbers_a.state.loaded
    assert not add_numbers_b.state.loaded
    assert not add_nodes.state.loaded

    project.run(eager=eager)
    if not eager:
        add_numbers_a.load()
        add_numbers_b.load()
        add_nodes.load()
    assert add_numbers_a.c == 3
    assert add_numbers_a.state.loaded
    assert add_numbers_b.c == 4
    assert add_numbers_b.state.loaded
    assert add_nodes.c == 7
    assert add_nodes.state.loaded


@pytest.mark.parametrize("eager", [True, False])
def test_AddNodeAttributes(proj_path, eager):
    with zntrack.Project() as project:
        add_numbers_a = AddNumbers(a=1, b=2, name="AddNumbersA")
        add_numbers_b = AddNumbers(a=1, b=3, name="AddNumbersB")
        add_nodes = AddNodeAttributes(a=add_numbers_a.c, b=add_numbers_b.c)

    assert not add_numbers_a.state.loaded
    assert not add_numbers_b.state.loaded
    assert not add_nodes.state.loaded

    project.run(eager=eager)
    if not eager:
        add_numbers_a.load()
        add_numbers_b.load()
        add_nodes.load()
    assert add_numbers_a.c == 3
    assert add_numbers_a.state.loaded
    assert add_numbers_b.c == 4
    assert add_numbers_b.state.loaded
    assert add_nodes.c == 7
    assert add_nodes.state.loaded


def test_AddNodes_legacy(proj_path):
    add_numbers_a = AddNumbers(a=1, b=2, name="AddNumbersA")
    add_numbers_b = AddNumbers(a=1, b=3, name="AddNumbersB")
    add_nodes = AddNodeAttributes(a=add_numbers_a @ "c", b=add_numbers_b @ "c")

    add_numbers_a.write_graph()
    add_numbers_b.write_graph()
    add_nodes.write_graph()

    assert not add_numbers_a.state.loaded
    assert not add_numbers_b.state.loaded
    assert not add_nodes.state.loaded

    assert dvc.cli.main(["repro"]) == 0

    add_numbers_a.load()
    add_numbers_b.load()
    add_nodes.load()
    assert add_numbers_a.c == 3
    assert add_numbers_a.state.loaded
    assert add_numbers_b.c == 4
    assert add_numbers_b.state.loaded
    assert add_nodes.c == 7
    assert add_nodes.state.loaded


def test_AddNodeAttributes_legacy(proj_path):
    add_numbers_a = AddNumbers(a=1, b=2, name="AddNumbersA")
    add_numbers_b = AddNumbers(a=1, b=3, name="AddNumbersB")
    add_nodes = AddNodes(a=add_numbers_a, b=add_numbers_b)

    add_numbers_a.write_graph()
    add_numbers_b.write_graph()
    add_nodes.write_graph()

    assert not add_numbers_a.state.loaded
    assert not add_numbers_b.state.loaded
    assert not add_nodes.state.loaded

    assert dvc.cli.main(["repro"]) == 0

    add_numbers_a.load()
    add_numbers_b.load()
    add_nodes.load()
    assert add_numbers_a.c == 3
    assert add_numbers_a.state.loaded
    assert add_numbers_b.c == 4
    assert add_numbers_b.state.loaded
    assert add_nodes.c == 7
    assert add_nodes.state.loaded
