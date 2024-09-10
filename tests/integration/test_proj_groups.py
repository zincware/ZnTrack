import subprocess

import pytest

import zntrack.examples


def test_groups_io(proj_path):
    project = zntrack.Project()

    with project:
        a = zntrack.examples.ParamsToOuts(params=1)

    with project.group("A"):
        b = zntrack.examples.AddOne(number=a.outs)

    with project.group("A"):
        c = zntrack.examples.AddOne(number=b.outs)

    with project.group("A", "B"):
        d = zntrack.examples.AddOne(number=c.outs)

    project.build()
    subprocess.check_call(["dvc", "repro"])

    assert a.state.group is None
    assert b.state.group.name == ("A",)
    assert c.state.group == b.state.group
    assert d.state.group.name == ("A", "B")

    assert a.outs == 1
    assert b.outs == 2
    assert c.outs == 3
    assert d.outs == 4

    assert a.name == "ParamsToOuts"
    assert b.name == "A_AddOne"
    assert c.name == "A_AddOne_1"
    assert d.name == "A_B_AddOne"

    assert len(b.state.group) == 2
    assert a not in b.state.group
    assert b in b.state.group
    assert c in b.state.group
    assert d not in b.state.group

    assert b.state.group["A_AddOne"] == b

    with pytest.raises(KeyError):
        b.state.group["NotExisting"]

    for node in d.state.group:
        assert node == d

    with pytest.raises(AttributeError):
        b.state.group.name = "Hello"

    with pytest.raises(AttributeError):
        b.state.group.nodes = []


def test_nested_groups(proj_path):
    # disabled from within znflow
    project = zntrack.Project()

    with project.group("A"):
        with pytest.raises(TypeError):
            with project.group("B"):
                pass
