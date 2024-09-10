import numpy as np
import pytest

import zntrack


class ComputeA(zntrack.Node):
    """Node stage A"""

    inp: int = zntrack.params()
    out: float = zntrack.outs()

    def run(self):
        self.out = np.power(2, self.inp).item()


class ComputeB(zntrack.Node):
    """Node stage B"""

    inp: int = zntrack.params()
    out: float = zntrack.outs()

    def run(self):
        self.out = np.power(3, self.inp).item()


class ComputeAB(zntrack.Node):
    """Node stage AB, depending on A&B"""

    a: ComputeA = zntrack.deps()
    b: ComputeB = zntrack.deps()
    param: str = zntrack.params("default")
    out: float = zntrack.outs()

    def run(self):
        self.out = self.a.out + self.b.out


def test_stage_addition(proj_path):
    """Check that the dvc repro works"""
    with zntrack.Project() as project:
        node_a = ComputeA(inp=2)
        node_b = ComputeB(inp=3)
        node_ab = ComputeAB(a=node_a, b=node_b)

    project.run()
    assert node_ab.out == 31


@pytest.mark.parametrize("eager", [True, False])
def test_stage_addition_run(proj_path, eager):
    """Adapted legacy tests"""
    with zntrack.Project() as project:
        a = ComputeA(inp=2)
        b = ComputeB(inp=3)
        ab = ComputeAB(a=a, b=b)

        a_named = ComputeA(inp=20)
        ab_named = ComputeAB(a=a_named, b=b)

    if eager:
        project.run()
    else:
        project.build()
        project.repro()

    assert ab.out == 31
    assert ab_named.out == 1048603