import pathlib

import pandas as pd
import pytest
import yaml

import zntrack
from zntrack.abc import Metrics

# from zntrack.utils import config, run_dvc_cmd # TODO ADD BACK
# TODO ADD ZNTRACK PLOTS

run_dvc_cmd = None
config = None


class NodeWithPlotsDVC(zntrack.Node):
    data: pd.DataFrame = zntrack.plots(
        zntrack.nwd / "data.csv",
        x="x",
        y="y",
        x_label="x",
        y_label="y",
        title="title",
        template="linear",
        use_global_plots=False,
    )

    def run(self) -> None:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        df.to_csv(self.data)

    def get_data(self):
        return pd.read_csv(self.data)


class NodeWithPlotsZn(zntrack.Node):
    data: pd.DataFrame = zntrack.plots(
        x="x",
        y="y",
        x_label="x",
        y_label="y",
        title="title",
        template="linear",
        use_global_plots=False,
    )

    def run(self) -> None:
        self.data = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

    def get_data(self):
        return self.data


class NodeWithPlotsZnGlobal(zntrack.Node):
    data: pd.DataFrame = zntrack.plots(
        x="x",
        y=["y", "z"],
        x_label="x",
        y_label="y",
        title="title",
        template="linear",
    )
    metrics: Metrics = zntrack.metrics()

    def run(self) -> None:
        self.data = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6], "z": [7, 8, 9]})
        self.metrics = {"a": 1, "b": 2}

    def get_data(self):
        return self.data


class NodeWithPlotsDVCGlobal(zntrack.Node):
    data: pd.DataFrame = zntrack.plots(
        zntrack.nwd / "data.csv",
        x="x",
        y=["y", "z"],
        x_label="x",
        y_label="y",
        title="title",
        template="linear",
    )
    metrics: Metrics = zntrack.metrics(zntrack.nwd / "metrics.json")

    def run(self) -> None:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6], "z": [7, 8, 9]})
        df.to_csv(self.data)
        self.metrics.write_text("{'a': 1, 'b': 2}")

    def get_data(self):
        return pd.read_csv(self.data)


class NodeRemoteTemplate(zntrack.Node):
    data: pd.DataFrame = zntrack.plots(
        zntrack.nwd / "data.csv",
        template=zntrack.__file__,
    )

    def run(self) -> None:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6], "z": [7, 8, 9]})
        df.to_csv(self.data)


@pytest.mark.parametrize("cls", [NodeWithPlotsDVC, NodeWithPlotsZn])
@pytest.mark.parametrize("eager", [True, False])
def test_NodeWithPlots(proj_path, eager, cls):
    with zntrack.Project() as project:
        node = cls()
    project.run(eager=eager)

    if not eager:
        node.load()
        dvc_dict = yaml.safe_load((proj_path / config.files.dvc).read_text())

        plots = {
            "x": "x",
            "y": "y",
            "x_label": "x",
            "y_label": "y",
            "title": "title",
            "template": "linear",
        }

        assert (
            dvc_dict["stages"][node.name]["plots"][0][f"nodes/{node.name}/data.csv"]
            == plots
        )
        run_dvc_cmd(["plots", "show"])

    if isinstance(node, NodeWithPlotsDVC):
        assert NodeWithPlotsDVC.from_rev().data == pathlib.Path(
            "nodes", node.name, "data.csv"
        )

    assert node.get_data()["x"].tolist() == [1, 2, 3]


@pytest.mark.parametrize("cls", [NodeWithPlotsZnGlobal, NodeWithPlotsDVCGlobal])
@pytest.mark.parametrize("eager", [True, False])
def test_NodeWithPlotsGlobal(proj_path, eager, cls):
    with zntrack.Project() as project:
        node = cls()
    project.run(eager=eager)

    if not eager:
        node.load()
        dvc_dict = yaml.safe_load((proj_path / config.files.dvc).read_text())

        plots = {
            "x": "x",
            "y": ["y", "z"],
            "x_label": "x",
            "y_label": "y",
            "title": "title",
            "template": "linear",
        }

        assert dvc_dict["plots"][0][f"nodes/{node.name}/data.csv"] == plots

        run_dvc_cmd(["plots", "show"])

    assert node.get_data()["x"].tolist() == [1, 2, 3]


def test_multiple_plots_nodes(proj_path):
    with zntrack.Project(automatic_node_names=True) as project:
        NodeWithPlotsZnGlobal()
        NodeWithPlotsZnGlobal()
        NodeWithPlotsDVCGlobal()
        a = NodeWithPlotsDVCGlobal()
    project.run()
    run_dvc_cmd(["plots", "show"])

    with project:
        NodeWithPlotsZnGlobal()
        b = NodeWithPlotsZnGlobal()
        NodeWithPlotsDVCGlobal()
        NodeWithPlotsDVCGlobal()
    project.run()
    run_dvc_cmd(["plots", "show"])
    # run_dvc_cmd(["repro", "-f"])

    # check loading
    NodeWithPlotsDVCGlobal.from_rev(name=a.name)
    NodeWithPlotsZnGlobal.from_rev(name=b.name)


def test_NodeRemoteTemplate(proj_path):
    with zntrack.Project(automatic_node_names=True) as project:
        NodeRemoteTemplate()
        NodeRemoteTemplate()
    project.run(repro=False)

    assert pathlib.Path("dvc_plots", "templates", "__init__.py").exists()
