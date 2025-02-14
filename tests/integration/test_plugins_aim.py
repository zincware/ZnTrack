import dataclasses
import os
import pathlib

import git
import numpy.testing as npt
import pandas as pd
import pytest
import yaml

import zntrack.examples

try:
    import aim
except ImportError:
    pytest.skip("aim is not installed", allow_module_level=True)


@dataclasses.dataclass
class T1:
    temperature: float


@dataclasses.dataclass
class T2:
    temperature: float


class MD(zntrack.Node):
    t: T1 | T2 | list = zntrack.deps()

    result: str = zntrack.outs()

    def run(self):
        self.result = self.t.__class__.__name__


class RangePlotter(zntrack.Node):
    start: int = zntrack.params()
    stop: int = zntrack.params()

    plots: pd.DataFrame = zntrack.plots(y="range")

    def run(self):
        self.plots = pd.DataFrame({"idx": list(range(self.start, self.stop))})


# fixture to set the os.env before the test and remove if after the test
@pytest.fixture
def aim_proj_path(proj_path):
    os.environ["ZNTRACK_PLUGINS"] = (
        "zntrack.plugins.dvc_plugin.DVCPlugin,zntrack.plugins.aim_plugin.AIMPlugin"
    )
    os.environ["AIM_TRACKING_URI"] = "aim://127.0.0.1:43800"

    config = {
        "global": {
            "ZNTRACK_PLUGINS": os.environ["ZNTRACK_PLUGINS"],
            "AIM_TRACKING_URI": os.environ["AIM_TRACKING_URI"],
        }
    }
    pathlib.Path("env.yaml").write_text(yaml.dump(config))

    yield proj_path

    del os.environ["ZNTRACK_PLUGINS"]
    del os.environ["AIM_TRACKING_URI"]


def test_aim_metrics(aim_proj_path):
    proj = zntrack.Project()

    with proj:
        node = zntrack.examples.ParamsToMetrics(params={"loss": 0})

    proj.build()
    # there should be no entry in the mlflow server

    proj.repro(build=False)
    # # the run should be there

    with node.state.plugins["AIMPlugin"].get_aim_run() as run:
        df = run.dataframe()
        assert df["dvc_stage_name"].tolist() == ["ParamsToMetrics"]
        assert df["dvc_stage_hash"].tolist() == [node.state.get_stage_hash()]
        assert df["zntrack_node"].tolist() == ["zntrack.examples.nodes.ParamsToMetrics"]
        assert df["params.loss"].tolist() == [0]

        # metrics
        metrics = {}
        for metric in run.metrics():
            metrics[metric.name] = list(metric.data.values())[0]

        npt.assert_array_equal(metrics["metrics.loss"], [[0]])

    # make a git commit with all the changes
    proj.finalize(msg="test")
    repo = git.Repo()

    with node.state.plugins["AIMPlugin"].get_aim_run() as run:
        df = run.dataframe()
        assert df["dvc_stage_name"].tolist() == ["ParamsToMetrics"]
        assert df["dvc_stage_hash"].tolist() == [node.state.get_stage_hash()]
        assert df["zntrack_node"].tolist() == ["zntrack.examples.nodes.ParamsToMetrics"]
        assert df["params.loss"].tolist() == [0]
        assert df["git_commit_message"].tolist() == ["test"]
        assert df["git_commit_hash"].tolist() == [repo.head.commit.hexsha]


def test_aim_plotting(aim_proj_path):
    proj = zntrack.Project()

    with proj:
        node = RangePlotter(start=0, stop=10)

    proj.build()
    proj.repro(build=False)

    with node.state.plugins["AIMPlugin"].get_aim_run() as run:
        df = run.dataframe()
        assert df["dvc_stage_name"].tolist() == ["RangePlotter"]
        assert df["dvc_stage_hash"].tolist() == [node.state.get_stage_hash()]
        assert df["zntrack_node"].tolist() == ["test_plugins_aim.RangePlotter"]

        # metrics
        metrics = {}
        for metric in run.metrics():
            metrics[metric.name] = list(metric.data.values())[0]
        npt.assert_array_equal(metrics["plots.idx"], [list(range(10))])

    proj.finalize(msg="test")
    repo = git.Repo()

    with node.state.plugins["AIMPlugin"].get_aim_run() as run:
        df = run.dataframe()
        assert df["git_commit_message"].tolist() == ["test"]
        assert df["git_commit_hash"].tolist() == [repo.head.commit.hexsha]


def test_multiple_nodes(aim_proj_path):
    with zntrack.Project() as proj:
        a = zntrack.examples.ParamsToOuts(params=3)
        b = zntrack.examples.ParamsToOuts(params=7)
        c = zntrack.examples.SumNodeAttributesToMetrics(inputs=[a.outs, b.outs], shift=0)

    proj.repro()

    with c.state.plugins["AIMPlugin"].get_aim_run() as run:
        metrics = {}
        for metric in run.metrics():
            metrics[metric.name] = list(metric.data.values())[0]

        npt.assert_array_equal(metrics["metrics.value"], [[10.0]])

    with b.state.plugins["AIMPlugin"].get_aim_run() as run:
        b_run_id = run.hash

    proj.finalize(msg="exp1")
    repo = git.Repo()

    a.params = 5
    proj.repro()

    proj.finalize(msg="exp2")
    repo = git.Repo()

    a = a.from_rev(a.name)
    b = b.from_rev(b.name)
    c = c.from_rev(c.name)

    aim_repo = aim.Repo(path=os.environ["AIM_TRACKING_URI"])
    for run_metrics_col in aim_repo.query_metrics(
        (
            f"run.dvc_stage_name == '{a.name}' and "
            f"run.git_commit_hash == '{repo.head.commit.hexsha}'"
        )
    ).iter():
        assert "original_run_id" not in run_metrics_col.run.dataframe().columns

    for run_metrics_col in aim_repo.query_metrics(
        (
            f"run.dvc_stage_name == '{c.name}' and "
            f"run.git_commit_hash == '{repo.head.commit.hexsha}'"
        )
    ).iter():
        assert "original_run_id" not in run_metrics_col.run.dataframe().columns

    for run_metrics_col in aim_repo.query_metrics(
        (
            f"run.dvc_stage_name == '{b.name}' and "
            f"run.git_commit_hash == '{repo.head.commit.hexsha}'"
        )
    ).iter():
        assert run_metrics_col.run.dataframe()["original_run_id"].tolist() == [b_run_id]


def test_project_tags(aim_proj_path):
    with zntrack.Project(tags={"lorem": "ipsum", "hello": "world"}) as proj:
        a = zntrack.examples.ParamsToOuts(params=3)
        b = zntrack.examples.ParamsToOuts(params=7)
        zntrack.examples.SumNodeAttributesToMetrics(inputs=[a.outs, b.outs], shift=0)

    proj.repro()

    with a.state.plugins["AIMPlugin"].get_aim_run() as run:
        run: aim.Run
        assert set(run.tags) == {"lorem=ipsum", "hello=world"}


def test_dataclass_deps(aim_proj_path):
    t1 = T1(temperature=1)
    t2 = T2(temperature=1)

    with zntrack.Project() as proj:
        md = MD(t=t1)

    proj.repro()

    with md.state.plugins["AIMPlugin"].get_aim_run() as run:
        df = run.dataframe()
        assert df["t.temperature"].tolist() == [1.0]
        assert df["t._cls"].tolist() == ["test_plugins_aim.T1"]

    proj.finalize(msg="test")
    repo = git.Repo()

    md.t = t2
    proj.repro()

    with md.from_rev().state.plugins["AIMPlugin"].get_aim_run() as run:
        df = run.dataframe()
        assert df["t.temperature"].tolist() == [1.0]
        assert df["t._cls"].tolist() == ["test_plugins_aim.T2"]

    repo = git.Repo()
    repo.git.add(".")
    repo.git.commit("-m", "test")
    proj.finalize()

    md.t = [t1, t2]
    proj.repro()

    with md.from_rev().state.plugins["AIMPlugin"].get_aim_run() as run:
        df = run.dataframe()
        assert df["t"].tolist() == [
            (
                '[{"_cls": "test_plugins_aim.T1", "temperature": 1},'
                ' {"_cls": "test_plugins_aim.T2", "temperature": 1}]'
            )
        ]
