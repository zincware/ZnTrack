import numpy as np
import pytest

import zntrack


class ComputeA(zntrack.Node):
    """Node stage A"""

    inp = zntrack.zn.params()
    out = zntrack.zn.outs()

    def __init__(self, inp=None, **kwargs):
        super().__init__(**kwargs)
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp).item()


class ComputeANamed(ComputeA):
    """Node stage A"""

    def __init__(self, **kwargs):
        kwargs["name"] = "Stage_A"
        super().__init__(**kwargs)


class ComputeB(zntrack.Node):
    """Node stage B"""

    inp = zntrack.zn.params()
    out = zntrack.zn.outs()

    def __init__(self, inp=None, **kwargs):
        super().__init__(**kwargs)
        self.inp = inp

    def run(self):
        self.out = np.power(3, self.inp).item()


class ComputeAB(zntrack.Node):
    """Node stage AB, depending on A&B"""

    a: ComputeA = zntrack.zn.deps()
    b: ComputeB = zntrack.zn.deps()
    out = zntrack.zn.outs()
    param = zntrack.zn.params("default")

    def run(self):
        self.out = self.a.out + self.b.out


class ComputeABNamed(ComputeAB):
    """Node stage AB, depending on A&B with a custom stage name"""

    def __init__(self, **kwargs):
        kwargs["name"] = "Stage_AB"
        super().__init__(**kwargs)


@pytest.mark.parametrize("cls_a", [ComputeA, ComputeANamed])
@pytest.mark.parametrize("cls_b", [ComputeB])
@pytest.mark.parametrize("cls_ab", [ComputeAB, ComputeABNamed])
def test_stage_addition(proj_path, cls_a, cls_b, cls_ab):
    """Check that the dvc repro works"""
    with zntrack.Project() as project:
        node_a = cls_a(inp=2)
        node_b = cls_b(inp=3)
        node_ab = cls_ab(a=node_a, b=node_b)

    project.run()
    node_ab.load()
    assert node_ab.out == 31


@pytest.mark.parametrize("eager", [True, False])
def test_stage_addition_run(proj_path, eager):
    """Adapted legacy tests"""
    with zntrack.Project() as project:
        a = ComputeA(inp=2)
        b = ComputeB(inp=3)
        ab = ComputeAB(a=a, b=b)

        a_named = ComputeANamed(inp=20)
        ab_named = ComputeABNamed(a=a_named, b=b)

    project.run(eager=eager)
    if not eager:
        ab.load()
        ab_named.load()
    assert ab.out == 31
    assert ab_named.out == 1048603
