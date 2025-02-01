import subprocess

import pandas as pd

import zntrack


class PandasPlotNode(zntrack.Node):
    n: int = zntrack.params()

    plot: pd.DataFrame = zntrack.plots(y="y", x="x")

    def run(self):
        self.plot = pd.DataFrame({"x": range(self.n), "y": range(self.n)})


class AutoSavePandasPlotNode(zntrack.Node):
    n: int = zntrack.params()

    plot: pd.DataFrame = zntrack.plots(y="y", x="x", autosave=True)

    def run(self):
        self.plot = pd.DataFrame({"x": [], "y": []})
        for i in range(self.n):
            self.plot = pd.concat([self.plot, pd.DataFrame({"x": [i], "y": [i]})])
            with (self.nwd / "plot.csv").open("r") as f:
                df = pd.read_csv(f, index_col=0)
                assert len(df) == i + 1
                assert len(self.plot) == i + 1
                assert df.equals(self.plot)


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


def test_multiple_plots(proj_path):
    with zntrack.Project() as proj:
        n1 = PandasPlotNode(n=10)
        n2 = PandasPlotNode(n=20)
        n3 = PandasPlotNode(n=30)

    proj.build()
    subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)

    for idx, node in enumerate([n1, n2, n3]):
        df = pd.read_csv(node.nwd / "plot.csv")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10 * (idx + 1)

        assert isinstance(node.plot, pd.DataFrame)
        assert len(node.plot) == 10 * (idx + 1)

        # create a new instance (lazy loading)
        node = node.from_rev(node.name)
        assert isinstance(node.plot, pd.DataFrame)
        assert len(node.plot) == 10 * (idx + 1)


def test_groups(proj_path):
    project = zntrack.Project()
    with project.group("group1"):
        n1 = PandasPlotNode(n=10)
        n2 = PandasPlotNode(n=20)
    with project.group("group2"):
        n3 = PandasPlotNode(n=30)
        n4 = PandasPlotNode(n=40)

    project.build()
    subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)

    for idx, node in enumerate([n1, n2, n3, n4]):
        df = pd.read_csv(node.nwd / "plot.csv")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10 * (idx + 1)

        assert isinstance(node.plot, pd.DataFrame)
        assert len(node.plot) == 10 * (idx + 1)

        # create a new instance (lazy loading)
        node = node.from_rev(node.name)
        assert isinstance(node.plot, pd.DataFrame)
        assert len(node.plot) == 10 * (idx + 1)


def test_autosave(proj_path):
    with zntrack.Project() as proj:
        AutoSavePandasPlotNode(n=10)

    proj.build()
    subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)
