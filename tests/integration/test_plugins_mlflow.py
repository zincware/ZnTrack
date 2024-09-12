import os
import pathlib
import uuid

import mlflow
import pytest
import yaml

import zntrack.examples


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
    # del os.environ["MLFLOW_EXPERIMENT_NAME"]


def test_mlflow_metrics(mlflow_proj_path):
    proj = zntrack.Project()

    with proj:
        node = zntrack.examples.ParamsToOuts(params=1)

    proj.repro()

    # list all mlflow runs under the active experiment
    runs = mlflow.search_runs()
    # one parent and one child run
    assert len(runs) == 2
