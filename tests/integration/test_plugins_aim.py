import os
import pathlib

import aim
import git
import numpy.testing as npt
import pytest
import yaml

import zntrack.examples


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
        assert df["zntrack_node"].tolist() == ["zntrack.examples.ParamsToMetrics"]
        assert df["params.loss"].tolist() == [0]

        # metrics
        metrics = {}
        for metric in run.metrics():
            metrics[metric.name] = list(metric.data.values())[0]

        npt.assert_array_equal(metrics["metrics.loss"], [[0]])

    # make a git commit with all the changes
    repo = git.Repo()
    repo.git.add(".")
    repo.git.commit("-m", "test")
    proj.finalize()

    with node.state.plugins["AIMPlugin"].get_aim_run() as run:
        df = run.dataframe()
        assert df["dvc_stage_name"].tolist() == ["ParamsToMetrics"]
        assert df["dvc_stage_hash"].tolist() == [node.state.get_stage_hash()]
        assert df["zntrack_node"].tolist() == ["zntrack.examples.ParamsToMetrics"]
        assert df["params.loss"].tolist() == [0]
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

    repo = git.Repo()
    repo.git.add(".")
    repo.git.commit("-m", "exp1")
    proj.finalize()

    a.params = 5
    proj.repro()

    repo = git.Repo()
    repo.git.add(".")
    repo.git.commit("-m", "exp2")
    proj.finalize()

    a = a.from_rev(a.name)
    b = b.from_rev(b.name)
    c = c.from_rev(c.name)

    aim_repo = aim.Repo(path=os.environ["AIM_TRACKING_URI"])
    for run_metrics_col in aim_repo.query_metrics(
        f"run.dvc_stage_name == '{a.name}' and run.git_commit_hash == '{repo.head.commit.hexsha}'"
    ).iter():
        assert "original_run_id" not in run_metrics_col.run.dataframe().columns

    for run_metrics_col in aim_repo.query_metrics(
        f"run.dvc_stage_name == '{c.name}' and run.git_commit_hash == '{repo.head.commit.hexsha}'"
    ).iter():
        assert "original_run_id" not in run_metrics_col.run.dataframe().columns

    for run_metrics_col in aim_repo.query_metrics(
        f"run.dvc_stage_name == '{b.name}' and run.git_commit_hash == '{repo.head.commit.hexsha}'"
    ).iter():
        assert run_metrics_col.run.dataframe()["original_run_id"].tolist() == [b_run_id]
