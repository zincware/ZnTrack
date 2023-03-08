import pathlib
import subprocess

import pandas as pd
import pandas.testing as pdt
import pytest
import yaml

import zntrack


class WritePlots(zntrack.Node):
    plots: pd.DataFrame = zntrack.zn.plots()

    def run(self):
        self.plots = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})


@pytest.mark.parametrize("eager", [True, False])
def test_WritePlots(proj_path, eager):
    with zntrack.Project() as project:
        plots = WritePlots()

    assert not plots.state.loaded

    project.run(eager=eager)
    if not eager:
        plots.load()
    pdt.assert_frame_equal(plots.plots, pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}))
