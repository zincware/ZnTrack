import subprocess

import numpy as np

import zntrack


class ParamsToNumpy(zntrack.Node):
    stop: int = zntrack.params()

    result: np.ndarray = zntrack.outs()

    def run(self):
        self.result = np.arange(self.stop)


def test_ParamsToNumpy(proj_path):
    with zntrack.Project() as proj:
        node = ParamsToNumpy(stop=10)

    proj.build()
    subprocess.check_call(["dvc", "repro"])

    node = zntrack.from_rev(node.name)
    assert np.all(node.result == np.arange(node.stop))
