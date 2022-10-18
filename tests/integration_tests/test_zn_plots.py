import pathlib
import subprocess

import pandas as pd
import pytest
import yaml

from zntrack import Node, dvc, zn


class WritePlots(Node):
    plots: pd.DataFrame = zn.plots()

    def run(self):
        self.plots = pd.DataFrame({"value": list(range(100))})
        self.plots.index.name = "my_index"


class WritePlotsNoCache(WritePlots):
    plots = zn.plots(cache=False)


class WritePlotsNoIndex(Node):
    plots: pd.DataFrame = zn.plots()

    def run(self):
        self.plots = pd.DataFrame({"value": list(range(100))})


class WritePlotsWrongData(Node):
    plots: pd.DataFrame = zn.plots()

    def run(self):
        self.plots = {"value": list(range(100))}


@pytest.mark.parametrize(
    ("PlotsCls", "cache"), [(WritePlots, True), (WritePlotsNoCache, False)]
)
def test_write_plots(proj_path, PlotsCls, cache):
    PlotsCls().write_graph(run=True)
    subprocess.check_call(["dvc", "plots", "show"])

    wp = PlotsCls.load()
    assert wp.plots.index.name == "my_index"
    plots_file = PlotsCls.plots.get_filename(wp)
    if cache:
        _ = subprocess.check_call(["git", "check-ignore", plots_file])
    else:
        with pytest.raises(subprocess.CalledProcessError):
            _ = subprocess.check_call(["git", "check-ignore", plots_file])


def test_plots_default():
    with pytest.raises(ValueError):

        class WrongDefaultNode1(Node):
            plots = zn.plots(pd.DataFrame({"value": list(range(100))}))

    with pytest.raises(ValueError):

        class WrongDefaultNode2(Node):
            plots = zn.plots(pd.DataFrame({"value": list(range(100))}), cache=False)


def test_load_plots(proj_path):
    WritePlots().run_and_save()

    df = pd.DataFrame({"value": list(range(100))})
    df.index.name = "index"

    assert df.equals(WritePlots.load().plots)


def test_write_plots_value_error(proj_path):
    WritePlotsNoIndex().run_and_save()
    wpni = WritePlotsNoIndex.load()
    assert wpni.plots.index.name == "index"


def test_write_plots_type_error(proj_path):
    with pytest.raises(TypeError):
        WritePlotsWrongData().run_and_save()


def test_save_plots(proj_path):
    write_plots = WritePlots()
    write_plots.run()
    write_plots.save_plots()

    assert pathlib.Path("nodes/WritePlots/plots.csv").exists()


class WriteTwoPlots(Node):
    plots_a: pd.DataFrame = zn.plots()
    plots_b: pd.DataFrame = zn.plots()

    def run(self):
        self.plots_a = pd.DataFrame({"value": list(range(100))})
        self.plots_a.index.name = "my_index_a"

        self.plots_b = pd.DataFrame({"value": [-x for x in range(100)]})
        self.plots_b.index.name = "my_index_b"


def test_write_two_plots(proj_path):
    WriteTwoPlots().write_graph(no_exec=False)
    subprocess.check_call(["dvc", "plots", "show"])

    wp = WriteTwoPlots.load()
    assert wp.plots_a.index.name == "my_index_a"
    assert wp.plots_b.index.name == "my_index_b"

    assert pathlib.Path("nodes", "WriteTwoPlots", "plots_a.csv").exists()
    assert pathlib.Path("nodes", "WriteTwoPlots", "plots_b.csv").exists()


class WritePlotsModify(Node):
    plots = zn.plots(x_label="test_label", title="My Plot", template="smooth")

    def run(self):
        self.plots = pd.DataFrame({"value": list(range(100))})


class WritePlotsModifyDVC(Node):
    plots = dvc.plots(x_label="test_label", title="My Plot")

    def run(self):
        self.plots.write_text("this is a csv file")


def test_write_plots_modify(proj_path):
    WritePlotsModify().write_graph()

    dvc_config = yaml.safe_load(pathlib.Path("dvc.yaml").read_text())

    assert (
        dvc_config["stages"]["WritePlotsModify"]["plots"][0][
            "nodes/WritePlotsModify/plots.csv"
        ]["x_label"]
        == "test_label"
    )
    assert (
        dvc_config["stages"]["WritePlotsModify"]["plots"][0][
            "nodes/WritePlotsModify/plots.csv"
        ]["title"]
        == "My Plot"
    )

    assert (
        dvc_config["stages"]["WritePlotsModify"]["plots"][0][
            "nodes/WritePlotsModify/plots.csv"
        ]["template"]
        == "smooth"
    )


def test_WritePlotsModifyDVC(proj_path):
    WritePlotsModifyDVC(plots=pathlib.Path("out.csv")).write_graph(run=True)
    assert pathlib.Path("out.csv").exists()


def test_write_plots_modify_lists(proj_path):
    with pytest.raises(ValueError):
        WritePlotsModifyDVC(plots=["a.csv", "b.csv"]).write_graph()
