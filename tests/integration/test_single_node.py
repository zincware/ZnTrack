import pytest

import zntrack


class AddNumbers(zntrack.Node):
    a = zntrack.zn.params()
    b = zntrack.zn.params()
    c = zntrack.zn.outs()

    def run(self):
        self.c = self.a + self.b


@pytest.mark.parametrize("eager", [True, False])
def test_AddNumbers(proj_path, eager):
    with zntrack.Project(eager=eager) as project:
        add_numbers = AddNumbers(a=1, b=2)

    assert not add_numbers.state.loaded

    project.run()
    add_numbers.load()
    assert add_numbers.c == 3
    assert add_numbers.state.loaded


@pytest.mark.parametrize("eager", [True, False])
def test_AddNumbers_named(proj_path, eager):
    with zntrack.Project(eager=eager) as project:
        add_numbers_a = AddNumbers(a=1, b=2, name="NodeA")
        add_numbers_b = AddNumbers(a=1, b=2, name="NodeB")

    assert not add_numbers_a.state.loaded
    assert not add_numbers_b.state.loaded

    project.run()
    add_numbers_a.load()
    add_numbers_b.load()
    assert add_numbers_a.c == 3
    assert add_numbers_a.state.loaded
    assert add_numbers_b.c == 3
    assert add_numbers_b.state.loaded
