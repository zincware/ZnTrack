import os
import pathlib

import git
import numpy.testing as npt
import pytest
import yaml

import zntrack.examples

import aim



class MetricsNode(zntrack.Node):
    user: str = zntrack.params()
    age: int = zntrack.params()

    data: dict = zntrack.metrics()

    def run(self):
        # when using AIM, metrics can only be numeric
        self.data = {"age": self.age}


# fixture to set the os.env before the test and remove if after the test
@pytest.fixture
def aim_proj_path(proj_path):
    os.environ["ZNTRACK_PLUGINS"] = (
        "zntrack.plugins.dvc_plugin.DVCPlugin,zntrack.plugins.aim_plugin.AIMPlugin"
    )
    os.environ["AIM_TRACKING_URI"] = "aim://127.0.0.1:43800"
    # os.environ["MLFLOW_EXPERIMENT_NAME"] = f"test-{uuid.uuid4()}"

    config = {
        "global": {
            "ZNTRACK_PLUGINS": os.environ["ZNTRACK_PLUGINS"],
            "AIM_TRACKING_URI": os.environ["AIM_TRACKING_URI"],
            # "MLFLOW_EXPERIMENT_NAME": os.environ["MLFLOW_EXPERIMENT_NAME"],
        }
    }
    pathlib.Path("env.yaml").write_text(yaml.dump(config))

    yield proj_path

    del os.environ["ZNTRACK_PLUGINS"]
    del os.environ["AIM_TRACKING_URI"]
    # del os.environ["MLFLOW_EXPERIMENT_NAME"]


def test_aim_metrics(aim_proj_path):

    with zntrack.Project() as proj:
        node = zntrack.examples.ParamsToMetrics(params={"loss": 0})

    proj.build()
    proj.repro(build=False)

    # assert before commit causes strange issues

    # make a git commit with all the changes
    repo = git.Repo()
    repo.git.add(".")
    repo.git.commit("-m", "test")
    node.state.plugins["AIMPlugin"].finalize()

    node.state.plugins["AIMPlugin"]
    run = node.state.plugins["AIMPlugin"].get_aim_run()
    df = run.dataframe()
    assert df["dvc_stage_name"].tolist() == ["ParamsToMetrics"]
    assert df["dvc_stage_hash"].tolist() == [node.state.get_stage_hash()]
    assert df["zntrack_node"].tolist() == ["zntrack.examples.ParamsToMetrics"]
    assert df["params.loss"].tolist() == [0]
    assert df["git_commit_message"].tolist() == ["test"]
    assert df["git_commit_hash"].tolist() == [repo.head.commit.hexsha]

    # assert df["tags"]
    # assert df["name"]

    # metrics
    metrics = {}
    for metric in run.metrics():
        metrics[metric.name] = list(metric.data.values())[0]

    npt.assert_array_equal(metrics["metrics.loss"], [[0]])
