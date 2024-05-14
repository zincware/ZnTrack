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
