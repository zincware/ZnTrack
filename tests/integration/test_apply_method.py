"""Test the apply function."""

import pytest

import zntrack.examples


@pytest.mark.parametrize("eager", [True, False])
def test_apply(proj_path, eager) -> None:
    """Test the "zntrack.apply" function."""
    project = zntrack.Project()

    JoinedParamsToOuts = zntrack.apply(zntrack.examples.ParamsToOuts, "join")  # noqa N806

    with project:
        a = zntrack.examples.ParamsToOuts(params=["a", "b"])
        b = JoinedParamsToOuts(params=["a", "b"])
        c = zntrack.apply(zntrack.examples.ParamsToOuts, "join")(params=["a", "b", "c"])

    if eager:
        project.run()
    else:
        project.repro(build=True)

    assert a.outs == ["a", "b"]
    assert b.outs == "a-b"
    assert c.outs == "a-b-c"


@pytest.mark.parametrize("attribute", [True, False])
@pytest.mark.parametrize("eager", [True, False])
def test_deps_apply(proj_path, eager, attribute):
    """Test connecting applied nodes to other nodes."""
    project = zntrack.Project()

    JoinedParamsToOuts = zntrack.apply(zntrack.examples.ParamsToOuts, "join")  # noqa N806

    assert issubclass(JoinedParamsToOuts, zntrack.Node)

    with project:
        a = zntrack.examples.ParamsToOuts(params=["a", "b"])
        b = JoinedParamsToOuts(params=["a", "b"])
        c = zntrack.apply(zntrack.examples.ParamsToOuts, "join")(params=["a", "b", "c"])

        if attribute:
            x3 = zntrack.examples.AddNodeAttributes(a=b.outs, b=c.outs)
        else:
            x3 = zntrack.examples.AddNodes2(a=b, b=c)

    if eager:
        project.run()
    else:
        project.repro(build=True)

    assert isinstance(a, zntrack.Node)
    assert isinstance(b, zntrack.Node)
    assert isinstance(c, zntrack.Node)
    assert isinstance(x3, zntrack.Node)

    assert x3.c == "a-ba-b-c"
