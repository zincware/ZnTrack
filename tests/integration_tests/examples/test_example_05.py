import os
import shutil

import numpy as np

from zntrack import Node, ZnTrackProject, zn


class ComputeA(Node):
    """Node stage A"""

    inp = zn.params()
    out = zn.outs()

    def __init__(self, inp=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp)


def test_stage_addition(tmp_path):
    """Check that the dvc repro works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    ComputeA(inp=np.arange(5)).write_graph()

    project.run()
    project.repro()
    finished_stage = ComputeA.load()
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))


def test_stage_addition_run(tmp_path):
    """Check that the PyTracks run method works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA(inp=np.arange(5))

    a.run_and_save()

    finished_stage = ComputeA.load()
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))
