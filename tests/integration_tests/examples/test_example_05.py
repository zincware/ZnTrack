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
        self.out = np.power(2, self.inp)


def test_stage_addition(proj_path):
    """Check that the dvc repro works"""
    project = ZnTrackProject()

    ComputeA(inp=np.arange(5)).write_graph()

    project.run()
    project.repro()
    finished_stage = ComputeA.load()
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))


def test_stage_addition_run(proj_path):
    """Check that the PyTracks run method works"""
    a = ComputeA(inp=np.arange(5))

    a.save()  # need to save to access the parameters zn.params
    a.run_and_save()

    finished_stage = ComputeA.load(lazy=False)
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))
