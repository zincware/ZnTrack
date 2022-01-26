import os
import shutil
import subprocess

import pandas as pd
import pytest

from zntrack import Node, zn


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
        self.plots.index.name = "index"


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


def test_load_plots(proj_path):
    WritePlots().run_and_save()

    df = pd.DataFrame({"value": [x for x in range(100)]})
    df.index.name = "index"

    assert df.equals(WritePlots.load().plots)


def test_write_plots_value_error(proj_path):
    with pytest.raises(ValueError):
        WritePlotsNoIndex().run_and_save()


def test_write_plots_type_error(proj_path):
    with pytest.raises(TypeError):
        WritePlotsWrongData().run_and_save()
