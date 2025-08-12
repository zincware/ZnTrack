import pytest

import zntrack.examples
from zntrack.config import NodeStatusEnum


@pytest.mark.parametrize("eager", [True, False])
def test_AddNodes(proj_path, eager):
    with zntrack.Project() as project:
        add_numbers_a = zntrack.examples.AddNumbers(a=1, b=2, name="AddNumbersA")
        add_numbers_b = zntrack.examples.AddNumbers(a=1, b=3, name="AddNumbersB")
        add_nodes = zntrack.examples.AddNodes(a=add_numbers_a, b=add_numbers_b)

    assert add_numbers_a.state.state == NodeStatusEnum.CREATED
    assert add_numbers_b.state.state == NodeStatusEnum.CREATED
    assert add_nodes.state.state == NodeStatusEnum.CREATED

    if eager:
        project.run()
    else:
        project.repro()

    assert add_numbers_a.c == 3
    # TODO: Node status is not being updated when not using from_rev
    if eager:
        assert add_numbers_a.state.state == NodeStatusEnum.FINISHED
    assert add_numbers_b.c == 4
    if eager:
        assert add_numbers_b.state.state == NodeStatusEnum.FINISHED
    assert add_nodes.c == 7
    if eager:
        assert add_nodes.state.state == NodeStatusEnum.FINISHED


@pytest.mark.parametrize("eager", [True, False])
def test_AddNodeAttributes(proj_path, eager):
    with zntrack.Project() as project:
        add_numbers_a = zntrack.examples.AddNumbers(a=1, b=2, name="AddNumbersA")
        add_numbers_b = zntrack.examples.AddNumbers(a=1, b=3, name="AddNumbersB")
        add_nodes = zntrack.examples.AddNodeAttributes(
            a=add_numbers_a.c, b=add_numbers_b.c
        )

    if eager:
        project.run()
    else:
        project.repro()
    assert add_numbers_a.c == 3
    if eager:
        assert add_numbers_a.state.state == NodeStatusEnum.FINISHED
    assert add_numbers_b.c == 4
    if eager:
        assert add_numbers_b.state.state == NodeStatusEnum.FINISHED
    assert add_nodes.c == 7
    if eager:
        assert add_nodes.state.state == NodeStatusEnum.FINISHED


def test_AddNodes_legacy(proj_path):
    with zntrack.Project() as proj:
        add_numbers_a = zntrack.examples.AddNumbers(a=1, b=2, name="AddNumbersA")
        add_numbers_b = zntrack.examples.AddNumbers(a=1, b=3, name="AddNumbersB")
        add_nodes = zntrack.examples.AddNodeAttributes(
            a=add_numbers_a.c, b=add_numbers_b.c
        )

    proj.build()

    assert add_numbers_a.state.state == NodeStatusEnum.CREATED
    assert add_numbers_b.state.state == NodeStatusEnum.CREATED
    assert add_nodes.state.state == NodeStatusEnum.CREATED
    proj.repro(build=False)

    add_numbers_a = add_numbers_a.from_rev(name=add_numbers_a.name)
    add_numbers_b = add_numbers_b.from_rev(name=add_numbers_b.name)
    add_nodes = add_nodes.from_rev(name=add_nodes.name)

    assert add_numbers_a.c == 3
    assert add_numbers_a.state.state == NodeStatusEnum.FINISHED
    assert add_numbers_b.c == 4
    assert add_numbers_b.state.state == NodeStatusEnum.FINISHED
    assert add_nodes.c == 7
    assert add_nodes.state.state == NodeStatusEnum.FINISHED


def test_AddNodeAttributes_legacy(proj_path):
    with zntrack.Project() as proj:
        add_numbers_a = zntrack.examples.AddNumbers(a=1, b=2, name="AddNumbersA")
        add_numbers_b = zntrack.examples.AddNumbers(a=1, b=3, name="AddNumbersB")
        add_nodes = zntrack.examples.AddNodes(a=add_numbers_a, b=add_numbers_b)

    proj.build()

    assert add_numbers_a.state.state == NodeStatusEnum.CREATED
    assert add_numbers_b.state.state == NodeStatusEnum.CREATED
    assert add_nodes.state.state == NodeStatusEnum.CREATED

    proj.repro(build=False)

    add_numbers_a = add_numbers_a.from_rev(name=add_numbers_a.name)
    add_numbers_b = add_numbers_b.from_rev(name=add_numbers_b.name)
    add_nodes = add_nodes.from_rev(name=add_nodes.name)

    assert add_numbers_a.c == 3
    assert add_numbers_a.state.state == NodeStatusEnum.FINISHED
    assert add_numbers_b.c == 4
    assert add_numbers_b.state.state == NodeStatusEnum.FINISHED
    assert add_nodes.c == 7
    assert add_nodes.state.state == NodeStatusEnum.FINISHED


def test_OptionalDeps(proj_path):
    with zntrack.Project() as proj:
        add_numbers = zntrack.examples.AddNumbers(a=1, b=2)
        add_none = zntrack.examples.OptionalDeps()
        add_value = zntrack.examples.OptionalDeps(value=add_numbers.c)

    proj.run()

    assert add_numbers.c == 3
    assert add_none.result == 0.0
    assert add_value.result == 3.0
