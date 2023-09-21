"""Tests for 'zntrack.deps'-field which can be used as both `zntrack.zn.deps` and `zntrack.zn.nodes`."""

import zntrack.examples

# TODO: change the parameters, rerun and see if it updates!


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

    a.write_params(min=1, max=5, seed=31415)
    # b.write_params(min=5, max=10, seed=31415) # only change one of the two parameters

    project.repro()

    a.load()
    b.load()
    c.load()

    assert a.number == 5
    assert b.number == 10
    assert c.result == 15


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

    a.write_params(min=1, max=5, seed=31415)

    project.repro()

    c.load()
    assert c.result == 15


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

    a.write_params(min=1, max=5, seed=31415)

    project.repro()

    c.load()
    assert c.result == 15

    b.write_params(min=5, max=10, seed=31415)

    project.repro()

    b.load()
    c.load()

    assert b.number == 9
    assert c.result == 14


def test_named_parent(proj_path):
    project = zntrack.Project(automatic_node_names=True)

    a = zntrack.examples.ComputeRandomNumber(params_file="a.json")
    b = zntrack.examples.ComputeRandomNumber(params_file="b.json")

    with project:
        c = zntrack.examples.SumRandomNumbersNamed([a, b], name="c")

    a.write_params(min=1, max=5, seed=42)
    b.write_params(min=5, max=10, seed=42)

    project.run()

    c.load()
    assert c.name == "c"
    assert c.result == 11


def test_many_to_one(proj_path):
    project = zntrack.Project(automatic_node_names=True)

    a = zntrack.examples.ComputeRandomNumber(params_file="a.json")

    with project:
        b = zntrack.examples.SumRandomNumbers([a])
        c = zntrack.examples.SumRandomNumbers([a])

    a.write_params(min=1, max=5, seed=42)
    # here we have one parameter file for both b and c
    # so a change in 'a.json' will affect both 'b' and 'c

    project.run()

    b.load()
    c.load()

    assert b.result == 1
    assert c.result == 1

    a.write_params(min=1, max=5, seed=31415)

    project.repro()

    b.load()
    c.load()

    assert b.result == 5
    assert c.result == 5


def test_many_to_one_params(proj_path):
    project = zntrack.Project(automatic_node_names=True)

    a = zntrack.examples.ComputeRandomNumberWithParams(min=1, max=5, seed=42)

    with project:
        b = zntrack.examples.SumRandomNumbers([a])
        c = zntrack.examples.SumRandomNumbers([a])

    # here we create a deepcopy of 'a' for both 'b' and 'c'
    # so a change in 'a' will not affect 'b' and 'c'
    # and we can change the parameters in b.numbers[0] and c.numbers[0] independently

    project.run()

    b.load()
    c.load()

    assert b.result == 1
    assert c.result == 1

    assert b.name == "SumRandomNumbers"
    assert c.name == "SumRandomNumbers_1"

    assert b.numbers[0].name == f"{b.name}+numbers+0"
    assert c.numbers[0].name == f"{c.name}+numbers+0"

    b.numbers[0].min = 5
    b.numbers[0].max = 10
    b.numbers[0].seed = 42

    project.run()

    b.load()
    c.load()

    assert b.result == 10
    assert c.result == 1

    c.numbers[0].min = 5
    c.numbers[0].max = 10
    c.numbers[0].seed = 42

    project.run()

    b.load()
    c.load()

    assert b.result == 10
    assert c.result == 10
