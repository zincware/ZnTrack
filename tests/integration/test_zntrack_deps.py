"""Tests for 'zntrack.deps'-field which can be used as both
`zntrack.zn.deps` and `zntrack.zn.nodes`."""

import zntrack.examples

# TODO: change the parameters, rerun and see if it updates!


def test_as_deps(proj_path):
    """Test for 'zntrack.deps' acting as `zntrack.zn.deps`-like field."""
    project = zntrack.Project()

    with project:
        a = zntrack.examples.ComputeRandomNumber(params_file="a.json")
        b = zntrack.examples.ComputeRandomNumber(params_file="b.json")
        c = zntrack.examples.SumRandomNumbers(numbers=[a, b])

    project.build()

    a = a.from_rev(a.name)
    b = b.from_rev(b.name)

    a.write_params(min=1, max=5, seed=42)
    b.write_params(min=5, max=10, seed=42)

    project.repro(build=False)

    assert a.number == 1
    assert b.number == 10
    assert c.result == 11

    a.write_params(min=1, max=5, seed=31415)

    project.repro()

    a = a.from_rev(a.name)
    b = b.from_rev(b.name)
    c = c.from_rev(c.name)

    assert a.number == 5
    assert b.number == 10
    assert c.result == 15
