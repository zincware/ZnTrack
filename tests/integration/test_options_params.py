import numpy as np
import pytest
import yaml

import zntrack


class ComputeA(zntrack.Node):
    """Node stage A"""

    inp: np.ndarray = zntrack.params()
    out: np.ndarray = zntrack.outs()

    def run(self):
        self.out = np.power(2, self.inp)


def test_numpy_params(proj_path):
    """Check that the dvc repro works"""
    project = zntrack.Project()

    with project:
        ComputeA(inp=np.arange(5))

    with pytest.raises(yaml.representer.RepresenterError):
        project.repro()
