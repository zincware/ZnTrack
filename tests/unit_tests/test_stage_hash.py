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
    plot: int = zntrack.plots()


# TODO: test outside DVC repo


@pytest.mark.parametrize(
    ("node", "stage_hash"),
    [
        (Node, "99a611464d825d0c7f36cd406331e6e53f05b26a9b5084f336b3318ea1f15b36"),
        (
            NodeWithParameter,
            "8c8fb1673bb9cded1e75e807a82d2b6388055625f7c2dc2b02643b28943cc404",
        ),
        (
            NodeWithOuts,
            "77984ac3472e38f16e25592528143fbecf86cbd71bb9b7ff9cfff66043530f14",
        ),
        (
            NodeWithMetrics,
            "22877d83878b1fcd04c0a7261ab73dfed347e562b37b18e1df8c7828f6584410",
        ),
        (
            NodeWithPlots,
            "e173cec6feabe17cd071482d41f0047cdd9fa962e1855ff511499f9dac51c98b",
        ),
    ],
)
def test_get_stage_hash(proj_path, node, stage_hash):
    with zntrack.Project() as proj:
        node = node()

    proj.build()

    assert node.state.get_stage_hash() == stage_hash
