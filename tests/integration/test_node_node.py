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
