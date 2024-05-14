"""Test the apply function."""

import zntrack.examples


def test_apply(proj_path) -> None:
    """Test the "zntrack.apply" function."""
    project = zntrack.Project()

    JoinedParamsToOuts = zntrack.apply(zntrack.examples.ParamsToOuts, "join")

    with project:
        a = zntrack.examples.ParamsToOuts(params=["a", "b"])
        b = JoinedParamsToOuts(params=["a", "b"])
        c = zntrack.apply(zntrack.examples.ParamsToOuts, "join")(params=["a", "b", "c"])

    project.run()

    a.load()
    b.load()
    c.load()

    assert a.outs == ["a", "b"]
    assert b.outs == "a-b"
    assert c.outs == "a-b-c"
