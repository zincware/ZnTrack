import numpy as np

import zntrack


class ComputeA(zntrack.Node):
    """Node stage A"""

    inp = zntrack.zn.params()
    out = zntrack.zn.outs()

    def __init__(self, inp=None, **kwargs):
        super().__init__(**kwargs)
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp)


def test_stage_addition(proj_path):
    """Check that the dvc repro works"""
    project = zntrack.Project()

    ComputeA(inp=np.arange(5)).write_graph()

    project.run()
    finished_stage = ComputeA.from_rev()
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))


def test_stage_addition_run(proj_path):
    """Check that the PyTracks run method works"""
    a = ComputeA(inp=np.arange(5))

    a.run()
    a.save()

    finished_stage = ComputeA.from_rev(lazy=False)
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))
