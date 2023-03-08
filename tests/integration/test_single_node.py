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
    with zntrack.Project() as project:
        add_numbers = AddNumbers(a=1, b=2)

    assert not add_numbers.state.loaded

    project.run(eager=eager)
    if not eager:
        add_numbers.load()
    assert add_numbers.c == 3
    assert add_numbers.state.loaded


@pytest.mark.parametrize("eager", [True, False])
def test_AddNumbers_named(proj_path, eager):
    with zntrack.Project() as project:
        add_numbers_a = AddNumbers(a=1, b=2, name="NodeA")
        add_numbers_b = AddNumbers(a=1, b=2, name="NodeB")

    assert not add_numbers_a.state.loaded
    assert not add_numbers_b.state.loaded

    project.run(eager=eager)
    if not eager:
        add_numbers_a.load()
        add_numbers_b.load()
    assert add_numbers_a.c == 3
    assert add_numbers_a.state.loaded
    assert add_numbers_b.c == 3
    assert add_numbers_b.state.loaded


class NodeWithInit(zntrack.Node):
    params = zntrack.zn.params()
    outs = zntrack.zn.outs()

    def __init__(self, params=None, **kwargs):
        # This test only works, because we don't have any non-default parameters
        # It is highly recommended to use '_post_init_' instead.
        super().__init__(**kwargs)
        self.params = params
        self.value = 42

    def run(self) -> None:
        self.outs = self.params


class NodeWithPostInit(zntrack.Node):
    params = zntrack.zn.params()
    outs = zntrack.zn.outs()

    def _post_init_(self):
        _ = self.params
        self.value = 42

    def run(self) -> None:
        self.outs = self.params


@pytest.mark.parametrize("cls", [NodeWithInit, NodeWithPostInit])
def test_NodeWithInit(proj_path, cls):
    with zntrack.Project() as project:
        node = cls(params=10)
    project.run()

    node = cls.from_rev()
    assert node.value == 42
    assert node.outs == 10


class NonDefaultInit(zntrack.Node):
    params = zntrack.zn.params()
    outs = zntrack.zn.outs()

    def __init__(self, params, **kwargs):
        super().__init__(**kwargs)
        self.params = params
        self.value = 42

    def run(self) -> None:
        self.outs = self.params


def test_NonDefaultInit(proj_path):
    with zntrack.Project() as project:
        node = NonDefaultInit(params=10)
    project.run()

    node = NonDefaultInit.from_rev()
    with pytest.raises(AttributeError):
        """We can not load an __init__ with non-default parameters"""
        assert node.value == 42
    assert node.outs == 10
