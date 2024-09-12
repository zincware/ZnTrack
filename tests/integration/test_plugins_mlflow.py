import os
import pathlib
import uuid

import git
import mlflow
import pandas as pd
import pytest
import yaml

import zntrack.examples


class RangePlotter(zntrack.Node):
    start: int = zntrack.params()
    stop: int = zntrack.params()

    plots: pd.DataFrame = zntrack.plots(y="range")

    def run(self):
        for idx in range(self.start, self.stop):
            self.state.extend_plots("plots", {"idx": idx})


@pytest.fixture
def mlflow_proj_path(proj_path):
    os.environ["ZNTRACK_PLUGINS"] = (
        "zntrack.plugins.dvc_plugin.DVCPlugin,zntrack.plugins.mlflow_plugin.MLFlowPlugin"
    )
    os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5000"
    os.environ["MLFLOW_EXPERIMENT_NAME"] = f"test-{uuid.uuid4()}"

    config = {
        "global": {
            "ZNTRACK_PLUGINS": os.environ["ZNTRACK_PLUGINS"],
            "MLFLOW_TRACKING_URI": os.environ["MLFLOW_TRACKING_URI"],
            "MLFLOW_EXPERIMENT_NAME": os.environ["MLFLOW_EXPERIMENT_NAME"],
        }
    }
    pathlib.Path("env.yaml").write_text(yaml.dump(config))

    yield proj_path

    del os.environ["ZNTRACK_PLUGINS"]
    del os.environ["MLFLOW_TRACKING_URI"]
    del os.environ["MLFLOW_EXPERIMENT_NAME"]


def test_mlflow_metrics(mlflow_proj_path):
    proj = zntrack.Project()

    with proj:
        node = zntrack.examples.ParamsToMetrics(params={"loss": 0})

    proj.build()
    # there should be no entry in the mlflow server

    proj.repro(build=False)
    # # the run should be there

    with node.state.plugins["MLFlowPlugin"]:
        pass  # load run_id states

    child_run_id = node.state.plugins["MLFlowPlugin"].child_run_id
    parent_run_id = node.state.plugins["MLFlowPlugin"].parent_run_id

    assert child_run_id is not None
    assert parent_run_id is not None

    run = mlflow.get_run(child_run_id)
    # assert params are logged
    assert run.data.params == {"params": "{'loss': 0}"}  # this is strange!
    # assert tags
    assert run.data.tags["dvc_stage_name"] == "ParamsToMetrics"
    assert run.data.tags["dvc_stage_hash"] == node.state.get_stage_hash()
    assert run.data.tags["zntrack_node"] == "zntrack.examples.ParamsToMetrics"

    # assert metrics
    assert run.data.metrics == {"metrics.loss": 0.0}

    # make a git commit with all the changes
    repo = git.Repo()
    repo.git.add(".")
    repo.git.commit("-m", "test")
    node.state.plugins["MLFlowPlugin"].finalize()

    run = mlflow.get_run(child_run_id)  # need to query the run again

    assert run.data.tags["git_commit_message"] == "test"
    assert run.data.tags["git_hash"] == repo.head.commit.hexsha


def test_mlflow_plotting(mlflow_proj_path):
    proj = zntrack.Project()

    with proj:
        node = RangePlotter(start=0, stop=10)

    proj.build()
    proj.repro(build=False)

    with node.state.plugins["MLFlowPlugin"]:
        pass  # load run_id states

    child_run_id = node.state.plugins["MLFlowPlugin"].child_run_id
    parent_run_id = node.state.plugins["MLFlowPlugin"].parent_run_id

    assert child_run_id is not None
    assert parent_run_id is not None

    run = mlflow.get_run(child_run_id)
    # assert params are logged
    assert run.data.params == {"start": "0", "stop": "10"}
    # assert tags
    assert run.data.tags["dvc_stage_name"] == "RangePlotter"
    assert run.data.tags["dvc_stage_hash"] == node.state.get_stage_hash()
    assert run.data.tags["zntrack_node"] == "test_plugins_mlflow.RangePlotter"

    # assert metrics (last)
    assert run.data.metrics == {"plots.idx": 9.0}

    client = mlflow.MlflowClient()
    history = client.get_metric_history(child_run_id, "plots.idx")
    assert len(history) == 10
    assert [entry.value for entry in history] == list(range(10))

    # make a git commit with all the changes
    repo = git.Repo()
    repo.git.add(".")
    repo.git.commit("-m", "test")
    node.state.plugins["MLFlowPlugin"].finalize()

    run = mlflow.get_run(child_run_id)  # need to query the run again

    assert run.data.tags["git_commit_message"] == "test"
    assert run.data.tags["git_hash"] == repo.head.commit.hexsha


# TODO: test multiple nodes
# TODO: test changes within one but not both nodes between commits
# TODO: test plots via extend_plots and via setting them at the end
# TODO: test project tags
