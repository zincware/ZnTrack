import subprocess

import pandas as pd

import zntrack


class PandasPlotNode(zntrack.Node):
    n: int = zntrack.params()

    plot: pd.DataFrame = zntrack.plots()

    def run(self):
        self.plot = pd.DataFrame({"x": range(self.n), "y": range(self.n)})


def test_simple_plot(proj_path):
    with zntrack.Project() as proj:
        node = PandasPlotNode(n=10)

    proj.build()
    subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)

    df = pd.read_csv(node.nwd / "plot.csv")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10

    assert isinstance(node.plot, pd.DataFrame)
    assert len(node.plot) == 10

    # create a new instance (lazy loading)
    node = node.from_rev()
    assert isinstance(node.plot, pd.DataFrame)
    assert len(node.plot) == 10
