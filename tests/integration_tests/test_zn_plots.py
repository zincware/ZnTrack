import os
import pathlib
import shutil
import subprocess

import pandas as pd
import pytest

from zntrack import Node, dvc, zn


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class WritePlots(Node):
    plots: pd.DataFrame = zn.plots()

    def run(self):
        self.plots = pd.DataFrame({"value": [x for x in range(100)]})
        self.plots.index.name = "my_index"


class WritePlotsNoIndex(Node):
    plots: pd.DataFrame = zn.plots()

    def run(self):
        self.plots = pd.DataFrame({"value": [x for x in range(100)]})


class WritePlotsWrongData(Node):
    plots: pd.DataFrame = zn.plots()

    def run(self):
        self.plots = {"value": [x for x in range(100)]}


def test_write_plots(proj_path):
    WritePlots().write_graph(no_exec=False)
    subprocess.check_call(["dvc", "plots", "show"])

    wp = WritePlots.load()
    assert wp.plots.index.name == "my_index"


def test_load_plots(proj_path):
    WritePlots().run_and_save()

    df = pd.DataFrame({"value": [x for x in range(100)]})
    df.index.name = "index"

    assert df.equals(WritePlots.load().plots)


def test_write_plots_value_error(proj_path):
    WritePlotsNoIndex().run_and_save()
    wpni = WritePlotsNoIndex.load()
    assert wpni.plots.index.name == "index"


def test_write_plots_type_error(proj_path):
    with pytest.raises(TypeError):
        WritePlotsWrongData().run_and_save()


class WriteTwoPlots(Node):
    plots_a: pd.DataFrame = zn.plots()
    plots_b: pd.DataFrame = zn.plots()

    def run(self):
        self.plots_a = pd.DataFrame({"value": [x for x in range(100)]})
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
    plots = zn.plots(x_label="test_label", title="My Plot")

    def run(self):
        self.plots = pd.DataFrame({"value": [x for x in range(100)]})


class WritePlotsModifyDVC(Node):
    plots = dvc.plots(x_label="test_label", title="My Plot")

    def run(self):
        self.plots.write_text("this is a csv file")


def test_write_plots_modify(proj_path):
    WritePlotsModify().write_graph()

    assert "x_label: test_label" in pathlib.Path("dvc.yaml").read_text()
    assert "title: My Plot" in pathlib.Path("dvc.yaml").read_text()


def test_WritePlotsModifyDVC(proj_path):
    WritePlotsModifyDVC(plots=pathlib.Path("out.csv")).write_graph(run=True)
    assert pathlib.Path("out.csv").exists()


def test_write_plots_modify_lists(proj_path):
    with pytest.raises(ValueError):
        WritePlotsModifyDVC(plots=["a.csv", "b.csv"]).write_graph()
