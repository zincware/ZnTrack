import dvc.cli
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
        project.repro(build=True)

    assert add_numbers_a.c == 3
    assert add_numbers_a.state.state == NodeStatusEnum.FINISHED
    assert add_numbers_b.c == 4
    assert add_numbers_b.state.state == NodeStatusEnum.FINISHED
    assert add_nodes.c == 7
    assert add_nodes.state.state == NodeStatusEnum.FINISHED


@pytest.mark.parametrize("eager", [True, False])
def test_AddNodeAttributes(proj_path, eager):
    with zntrack.Project() as project:
        add_numbers_a = zntrack.examples.AddNumbers(a=1, b=2, name="AddNumbersA")
        add_numbers_b = zntrack.examples.AddNumbers(a=1, b=3, name="AddNumbersB")
        add_nodes = zntrack.examples.AddNodeAttributes(
            a=add_numbers_a.c, b=add_numbers_b.c
        )

    assert add_numbers_a.state.state == NodeStatusEnum.CREATED
    assert add_numbers_b.state.state == NodeStatusEnum.CREATED
    assert add_nodes.state.state == NodeStatusEnum.CREATED

    if eager:
        project.run()
    else:
        project.repro(build=True)

    assert add_numbers_a.c == 3
    assert add_numbers_a.state.state == NodeStatusEnum.FINISHED
    assert add_numbers_b.c == 4
    assert add_numbers_b.state.state == NodeStatusEnum.FINISHED
    assert add_nodes.c == 7
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

    assert dvc.cli.main(["repro"]) == 0

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

    assert not add_numbers_a.state.state == NodeStatusEnum.CREATED
    assert not add_numbers_b.state.state == NodeStatusEnum.CREATED
    assert not add_nodes.state.state == NodeStatusEnum.CREATED

    assert dvc.cli.main(["repro"]) == 0

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