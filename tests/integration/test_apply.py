"""Test the apply function."""

import pytest

import zntrack.examples


@pytest.mark.parametrize("eager", [True, False])
def test_apply(proj_path, eager) -> None:
    """Test the "zntrack.apply" function."""
    project = zntrack.Project()

    JoinedParamsToOuts = zntrack.apply(zntrack.examples.ParamsToOuts, "join")

    with project:
        a = zntrack.examples.ParamsToOuts(params=["a", "b"])
        b = JoinedParamsToOuts(params=["a", "b"])
        c = zntrack.apply(zntrack.examples.ParamsToOuts, "join")(params=["a", "b", "c"])

    project.run(eager=eager)

    a.load()
    b.load()
    c.load()

    assert a.outs == ["a", "b"]
    assert b.outs == "a-b"
    assert c.outs == "a-b-c"

@pytest.mark.parametrize("eager", [True, False])
def test_deps_apply(proj_path, eager):
    """Test connecting applied nodes to other nodes."""

    project = zntrack.Project()

    JoinedParamsToOuts = zntrack.apply(zntrack.examples.ParamsToOuts, "join")

    assert issubclass(JoinedParamsToOuts, zntrack.Node)

    with project:
        a = zntrack.examples.ParamsToOuts(params=["a", "b"])
        b = JoinedParamsToOuts(params=["a", "b"])
        c = zntrack.apply(zntrack.examples.ParamsToOuts, "join")(params=["a", "b", "c"])

        x3 = zntrack.examples.AddNumbers(a=b.outs, b=c.outs)

    project.run(eager=eager)

    x3.load()
    
    assert isinstance(a, zntrack.Node)
    assert isinstance(b, zntrack.Node)
    assert isinstance(c, zntrack.Node)
    assert isinstance(x3, zntrack.Node)

    assert x3.c == 'a-ba-b-c'
