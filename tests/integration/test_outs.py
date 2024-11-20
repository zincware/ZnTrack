import numpy as np

import zntrack


class NumpyToOuts(zntrack.Node):
    value: np.ndarray = zntrack.outs()

    def run(self):
        self.value = np.array([1, 2, 3])


def test_numpy_outs(proj_path):
    project = zntrack.Project()
    with project:
        n = NumpyToOuts()
    project.repro()

    assert n.value.tolist() == [1, 2, 3]
