import numpy as np

from zntrack import Node, ZnTrackProject, zn


class ComputeA(Node):
    """Node stage A"""

    inp = zn.params()
    out = zn.outs()

    def __init__(self, inp=None, **kwargs):
        super().__init__(**kwargs)
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp).item()


class ComputeB(Node):
    """Node stage B"""

    inp = zn.params()
    out = zn.outs()

    def __init__(self, inp=None, **kwargs):
        super().__init__(**kwargs)
        self.inp = inp

    def run(self):
        self.out = np.power(3, self.inp).item()


class ComputeAB(Node):
    """Node stage AB, depending on A&B"""

    a: ComputeA = zn.deps(ComputeA.load())
    b: ComputeB = zn.deps(ComputeB.load())
    out = zn.outs()
    param = zn.params("default")

    def run(self):
        self.out = self.a.out + self.b.out


class ComputeANamed(Node):
    """Node stage A"""

    inp = zn.params()
    out = zn.outs()

    def __init__(self, inp=None, **kwargs):
        kwargs["name"] = "Stage_A"
        super().__init__(**kwargs)
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp).item()


class ComputeABNamed(Node):
    """Node stage AB, depending on A&B with a custom stage name"""

    a: ComputeANamed = zn.deps(ComputeANamed.load())
    b: ComputeB = zn.deps(ComputeB.load())
    out = zn.outs()

    param = zn.params()

    def __init__(self, **kwargs):
        kwargs["name"] = "Stage_AB"
        super().__init__(**kwargs)
        self.param = "default"

    def run(self):
        self.out = self.a.out + self.b.out


def test_stage_addition(proj_path):
    """Check that the dvc repro works"""
    project = ZnTrackProject()
    project.name = "test01"

    ComputeA(inp=2).write_graph()
    ComputeB(inp=3).write_graph()
    ComputeAB().write_graph()

    project.run()
    project.repro()
    finished_stage = ComputeAB.load()
    assert finished_stage.out == 31


def test_stage_addition_named(proj_path):
    """Check that the dvc repro works with named stages"""
    project = ZnTrackProject()
    project.name = "test01"

    ComputeANamed(inp=2).write_graph()
    ComputeB(inp=3).write_graph()
    ComputeABNamed().write_graph()

    project.repro()
    finished_stage = ComputeABNamed.load()
    assert finished_stage.out == 31


def test_stage_addition_run(proj_path):
    """Check that the PyTracks run method works"""
    a = ComputeA(inp=2)
    a.run_and_save()  # I must save here, because of the dependency of the output in AB
    b = ComputeB(inp=3)
    b.run_and_save()

    ab = ComputeAB()
    ab.run_and_save()

    finished_stage = ComputeAB.load()
    assert finished_stage.out == 31


def test_stage_addition_named_run(proj_path):
    """Check that the PyTracks run method works with named stages"""
    ComputeANamed(inp=2).save()
    ComputeB(inp=3).save()
    ComputeAB().save()
    ComputeABNamed().save()

    ComputeANamed.load().run_and_save()
    ComputeB.load().run_and_save()
    ComputeABNamed.load().run_and_save()

    finished_stage = ComputeABNamed.load()
    assert finished_stage.out == 31


def test_named_single_stage(proj_path):
    """Test a single named stage"""
    ComputeANamed(inp=2).write_graph(no_exec=False)

    assert ComputeANamed.load().out == 4
