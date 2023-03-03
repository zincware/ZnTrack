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
