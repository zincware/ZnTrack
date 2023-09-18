"""Tests for 'zntrack.deps'-field which can be used as both `zntrack.zn.deps` and `zntrack.zn.nodes`."""

import zntrack.examples


def test_as_deps(proj_path):
    """Test for 'zntrack.deps' acting as `zntrack.zn.deps`-like field."""
    project = zntrack.Project(automatic_node_names=True)

    with project:
        a = zntrack.examples.ComputeRandomNumber(params_file="a.json")
        b = zntrack.examples.ComputeRandomNumber(params_file="b.json")
        c = zntrack.examples.SumRandomNumbers([a, b])

    a.write_params(min=1, max=5, seed=42)
    b.write_params(min=5, max=10, seed=42)

    project.run()

    a.load()
    b.load()
    c.load()

    assert a.number == 1
    assert b.number == 10
    assert c.result == 11


def test_as_nodes(proj_path):
    """Test for 'zntrack.deps' acting as `zntrack.zn.nodes`-like field."""
    project = zntrack.Project(automatic_node_names=True)

    a = zntrack.examples.ComputeRandomNumber(params_file="a.json")
    b = zntrack.examples.ComputeRandomNumber(params_file="b.json")

    with project:
        c = zntrack.examples.SumRandomNumbers([a, b])

    a.write_params(min=1, max=5, seed=42)
    b.write_params(min=5, max=10, seed=42)

    project.run()

    # TODO: good error messages when someone tries to load a node that is not on the graph
    # a.load()
    # b.load()
    # assert a.number == 1
    # assert b.number == 10

    c.load()
    assert c.result == 11


def test_mixed(proj_path):
    project = zntrack.Project(automatic_node_names=True)

    a = zntrack.examples.ComputeRandomNumber(params_file="a.json")

    with project:
        b = zntrack.examples.ComputeRandomNumber(params_file="b.json")
        c = zntrack.examples.SumRandomNumbers([a, b])

    a.write_params(min=1, max=5, seed=42)
    b.write_params(min=5, max=10, seed=42)

    project.run()

    b.load()
    c.load()

    assert b.number == 10
    assert c.result == 11
