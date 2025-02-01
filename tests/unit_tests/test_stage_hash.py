import pandas as pd
import pytest

import zntrack


class Node(zntrack.Node):
    pass

    def run(self):
        pass


class NodeWithParameter(zntrack.Node):
    param: int = zntrack.params(default=1)

    def run(self):
        pass


class NodeWithOuts(zntrack.Node):
    out: int = zntrack.outs()

    def run(self):
        self.out = 1


class NodeWithMetrics(zntrack.Node):
    metric: dict = zntrack.metrics()

    def run(self):
        self.metric = {"y": 1}


class NodeWithPlots(zntrack.Node):
    plot: pd.DataFrame = zntrack.plots(y="y")

    def run(self):
        self.plot = pd.DataFrame({"y": [1]})


class NodeWithMetricsAndPlots(zntrack.Node):
    metric: dict = zntrack.metrics()
    plot: pd.DataFrame = zntrack.plots(y="y")

    def run(self):
        self.metric = {"y": 1}
        self.plot = pd.DataFrame({"y": [1]})


class NodeWithMetricsAndPlotsAndParams(zntrack.Node):
    metric: dict = zntrack.metrics()
    plot: pd.DataFrame = zntrack.plots(y="y")
    param: int = zntrack.params(default=1)

    def run(self):
        self.metric = {"y": 1}
        self.plot = pd.DataFrame({"y": [1]})


# TODO: test outside DVC repo


@pytest.mark.parametrize(
    ("node", "stage_hash", "full_stage_hash"),
    [
        (Node, "99a611464d", None),
        (NodeWithParameter, "8c8fb1673bb9", None),
        (NodeWithOuts, "77984ac3472e3", None),
        (NodeWithMetrics, "22877d83878b1", None),
        (NodeWithPlots, "e173cec6feabe", None),
        (NodeWithMetricsAndPlots, "a4b2aba9ec", None),
        (NodeWithMetricsAndPlotsAndParams, "b64bdd1da9", None),
    ],
)
def test_get_stage_hash(proj_path, node, stage_hash, full_stage_hash):
    with zntrack.Project() as proj:
        node = node()

    proj.build()

    assert node.state.get_stage_hash()[:10] == stage_hash[:10]

    proj.repro(build=False)

    assert node.from_rev().state.get_stage_hash()[:10] == stage_hash[:10]

    # TODO: this changes every run because of node_meta
    #  - do we want to exclude it - as it is the only output that is
    # by design non-deterministic!
    # assert node.from_rev().state.get_stage_hash(include_outs=True)[:10]
    #  == full_stage_hash[:10]
