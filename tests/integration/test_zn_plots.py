import pandas as pd
import pandas.testing as pdt
import pytest

import zntrack.examples
from zntrack.config import NodeStatusEnum


@pytest.mark.parametrize("eager", [True, False])
def test_WritePlots(proj_path, eager):
    with zntrack.Project() as project:
        plots = zntrack.examples.WritePlots()

    assert plots.state.state == NodeStatusEnum.CREATED

    if eager:
        project.run()
    else:
        project.repro()
    pdt.assert_frame_equal(plots.plots, pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}))
