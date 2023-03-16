"""Test for [NodeAttribute] as 'zn.deps'."""
import dvc.cli

from zntrack import Node, zn


class GenerateOutput(Node):
    """Generate an output."""

    inputs: int = zn.params()
    output: int = zn.outs()

    def run(self):
        self.output = self.inputs


class SumNumbers(Node):
    """Sum a list of numbers."""

    inputs: list = zn.deps()
    shift: int = zn.params()
    output: int = zn.outs()

    def run(self):
        self.output = sum(self.inputs) + self.shift


def test_list_deps(proj_path):
    node1 = GenerateOutput(inputs=1, name="node1")
    node2 = GenerateOutput(inputs=2, name="node2")

    data = [node1 @ "output", node2 @ "output"]
    node3 = SumNumbers(inputs=data, shift=10)

    node1.write_graph()
    node2.write_graph()
    node3.write_graph()

    assert dvc.cli.main(["repro"]) == 0

    node1.load()
    node2.load()
    node3.load()

    assert node1.output == 1
    assert node2.output == 2
    assert node3.output == 13
