import pytest

import zntrack


class Node(zntrack.Node):
    pass


class NodeWithParameter(zntrack.Node):
    param: int = zntrack.params(default=1)


class NodeWithOuts(zntrack.Node):
    out: int = zntrack.outs()


class NodeWithMetrics(zntrack.Node):
    metric: int = zntrack.metrics()


class NodeWithPlots(zntrack.Node):
    plot: int = zntrack.plots(y="y")


class NodeWithMetricsAndPlots(zntrack.Node):
    metric: int = zntrack.metrics()
    plot: int = zntrack.plots(y="y")


class NodeWithMetricsAndPlotsAndParams(zntrack.Node):
    metric: int = zntrack.metrics()
    plot: int = zntrack.plots(y="y")
    param: int = zntrack.params(default=1)


# TODO: test outside DVC repo


@pytest.mark.parametrize(
    ("node", "stage_hash"),
    [
        (Node, "99a611464d"),
        (
            NodeWithParameter,
            "8c8fb1673bb9",
        ),
        (
            NodeWithOuts,
            "77984ac3472e3",
        ),
        (
            NodeWithMetrics,
            "22877d83878b1",
        ),
        (
            NodeWithPlots,
            "e173cec6feabe",
        ),
        (
            NodeWithMetricsAndPlots,
            "a4b2aba9ec",
        ),
        (
            NodeWithMetricsAndPlotsAndParams,
            "b64bdd1da9",
        ),
    ],
)
def test_get_stage_hash(proj_path, node, stage_hash):
    with zntrack.Project() as proj:
        node = node()

    proj.build()

    assert node.state.get_stage_hash()[:10] == stage_hash[:10]
