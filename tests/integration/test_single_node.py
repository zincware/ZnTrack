import pathlib
import typing as t

import pytest
import yaml

import zntrack.examples
from zntrack.config import NodeStatusEnum


@pytest.mark.parametrize("eager", [True, False])
def test_AddNumbers(proj_path, eager):
    with zntrack.Project() as project:
        add_numbers = zntrack.examples.AddNumbers(a=1, b=2)

    assert add_numbers.state.state == NodeStatusEnum.CREATED

    if eager:
        project.run()
    else:
        project.repro()

    assert add_numbers.c == 3
    add_numbers = add_numbers.from_rev()
    assert add_numbers.c == 3
    assert add_numbers.state.state == NodeStatusEnum.FINISHED


def test_AddNumbers_remove_params(proj_path):
    with zntrack.Project() as project:
        add_numbers = zntrack.examples.AddNumbers(a=1, b=2)

    assert add_numbers.state.state == NodeStatusEnum.CREATED

    project.repro()

    params = pathlib.Path("params.yaml").read_text()
    params = yaml.safe_load(params)
    params[add_numbers.name] = {}
    params = pathlib.Path("params.yaml").write_text(yaml.dump(params))

    # with pytest.raises(zntrack.exceptions.NodeNotAvailableError):
    #     add_numbers.load()


def test_zntrack_from_rev(proj_path):
    with zntrack.Project() as project:
        add_numbers = zntrack.examples.AddNumbers(a=1, b=2)

    assert add_numbers.state.state == NodeStatusEnum.CREATED

    project.repro()

    node = zntrack.from_rev(add_numbers.name)
    assert node.a == 1
    assert node.b == 2
    assert node.c == 3
    assert node.state.state == NodeStatusEnum.FINISHED


@pytest.mark.parametrize("eager", [True, False])
def test_AddNumbers_named(proj_path, eager):
    with zntrack.Project() as project:
        add_numbers_a = zntrack.examples.AddNumbers(a=1, b=2, name="NodeA")
        add_numbers_b = zntrack.examples.AddNumbers(a=1, b=2, name="NodeB")

    assert add_numbers_a.state.state == NodeStatusEnum.CREATED
    assert add_numbers_b.state.state == NodeStatusEnum.CREATED

    if eager:
        project.run()
    else:
        project.repro()

    assert add_numbers_a.c == 3
    assert add_numbers_b.c == 3


class NodeWithPostInit(zntrack.Node):
    params: t.Any = zntrack.params()
    outs: t.Any = zntrack.outs()

    def __post_init__(self):
        # _ = self.params
        # the value is not loaded in the _post_init_
        self.value = 42

    def run(self) -> None:
        assert self.value == 42
        self.outs = self.params


@pytest.mark.parametrize("eager", [True, False])
def test_NodeWithPostInit(proj_path, eager):
    with zntrack.Project() as project:
        node = NodeWithPostInit(params=10)

    if eager:
        project.run()
    else:
        project.repro()
    node = NodeWithPostInit.from_rev()
    assert node.value == 42
    assert node.outs == 10


class NonDefaultInit(zntrack.Node):
    params: t.Any = zntrack.params()
    outs: t.Any = zntrack.outs()

    # def __init__(self, params, **kwargs):
    #     super().__init__(**kwargs)
    #     self.params = params
    #     self.value = 42

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


class NoOutsWritten(zntrack.Node):
    params: t.Any = zntrack.params()
    outs: t.Any = zntrack.outs()

    def run(self) -> None:
        pass


# @pytest.mark.parametrize("eager", [True, False])
# def test_NoOutsWritten(proj_path, eager):
#     with zntrack.Project() as project:
#         node = NoOutsWritten(params=10)
#     project.run(eager=eager)
#     if eager:
#         node.save()
#     else:
#         node.load()

#     node = NoOutsWritten.from_rev()
#     assert node.outs is None


def test_outs_in_init(proj_path):
    with pytest.raises(TypeError):
        # outs can not be set
        _ = zntrack.examples.AddNumbers(a=1, b=2, outs=3)
    with zntrack.Project():
        with pytest.raises(TypeError):
            # outs can not be set
            _ = zntrack.examples.AddNumbers(a=1, b=2, c=3)  # c is an output
