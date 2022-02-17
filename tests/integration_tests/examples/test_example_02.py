import os
import shutil

import numpy as np

from zntrack import Node, ZnTrackProject, dvc, zn


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

    a: ComputeA = dvc.deps(ComputeA.load())
    b: ComputeB = dvc.deps(ComputeB.load())
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

    a: ComputeANamed = dvc.deps(ComputeANamed.load())
    b: ComputeB = dvc.deps(ComputeB.load())
    out = zn.outs()

    param = dvc.params()

    def __init__(self, **kwargs):
        kwargs["name"] = "Stage_AB"
        super().__init__(**kwargs)
        self.param = "default"

    def run(self):
        self.out = self.a.out + self.b.out


def test_stage_addition(tmp_path):
    """Check that the dvc repro works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    ComputeA(inp=2).write_graph()
    ComputeB(inp=3).write_graph()
    ComputeAB().write_graph()

    project.run()
    project.repro()
    finished_stage = ComputeAB.load()
    assert finished_stage.out == 31


def test_stage_addition_named(tmp_path):
    """Check that the dvc repro works with named stages"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    ComputeANamed(inp=2).write_graph()
    ComputeB(inp=3).write_graph()
    ComputeABNamed().write_graph()

    project.repro()
    finished_stage = ComputeABNamed.load()
    assert finished_stage.out == 31


def test_stage_addition_run(tmp_path):
    """Check that the PyTracks run method works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA(inp=2)
    a.run_and_save()  # I must save here, because of the dependency of the output in AB
    b = ComputeB(inp=3)
    b.run_and_save()

    ab = ComputeAB()
    ab.run_and_save()

    finished_stage = ComputeAB.load()
    assert finished_stage.out == 31


def test_stage_addition_named_run(tmp_path):
    """Check that the PyTracks run method works with named stages"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    ComputeANamed(inp=2).save()
    ComputeB(inp=3).save()
    ComputeAB().save()
    ComputeABNamed().save()

    ComputeANamed.load().run_and_save()
    ComputeB.load().run_and_save()
    ComputeABNamed.load().run_and_save()

    finished_stage = ComputeABNamed.load()
    assert finished_stage.out == 31


def test_named_single_stage(tmp_path):
    """Test a single named stage"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    ComputeANamed(inp=2).write_graph(no_exec=False)

    assert ComputeANamed.load().out == 4
