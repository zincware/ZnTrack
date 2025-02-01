import pathlib

import zntrack.examples


def test_nodes_not_created(proj_path):
    project = zntrack.Project()

    with project:
        a = zntrack.examples.ParamsToOuts(
            params=42,
        )
        b = zntrack.examples.ParamsToOuts(
            params=18,
        )
        zntrack.examples.AddNodeAttributes(
            a=a.outs,
            b=b.outs,
        )

    with project.group("group"):
        d = zntrack.examples.ParamsToOuts(
            params=42,
        )
        e = zntrack.examples.ParamsToOuts(
            params=18,
        )
        zntrack.examples.AddNodeAttributes(
            a=d.outs,
            b=e.outs,
        )

    with project.group("plots"):
        zntrack.examples.WritePlots(
            x=[1, 2, 3],
            y=[4, 5, 6],
        )

    project.build()

    assert not pathlib.Path("nodes").exists()
