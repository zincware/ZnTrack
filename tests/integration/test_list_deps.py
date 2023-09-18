"""Test for [NodeAttribute] as 'zn.deps'."""
import dvc.cli

import zntrack.examples


def test_list_deps(proj_path):
    with zntrack.Project() as project:
        node1 = zntrack.examples.ParamsToOuts(params=1, name="node1")
        node2 = zntrack.examples.ParamsToOuts(params=2, name="node2")

        data = [node1.outs, node2.outs]
        node3 = zntrack.examples.SumNodeAttributes(data, shift=10)

    project.run()

    assert dvc.cli.main(["repro"]) == 0

    node1.load()
    node2.load()
    node3.load()

    assert node1.outs == 1
    assert node2.outs == 2
    assert node3.output == 13
