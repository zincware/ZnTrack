import os
import pathlib

import git
import numpy.testing as npt
import pytest
import yaml

import zntrack.examples

try:
    import aim
except ImportError:
    aim = None


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


@pytest.mark.skipif(aim is None, reason="Aim is not installed.")
def test_aim_metrics(aim_proj_path):

    with zntrack.Project() as proj:
        node = zntrack.examples.ParamsToMetrics(params={"loss": 0})

    proj.build()
    proj.repro(build=False)

    # with open(node.nwd / "data.json") as f:
    #     metrics = json.load(f)

    # assert metrics == {"age": 42}

    # run = node.state.plugins["AIMPlugin"].get_aim_run()
    # assert run["dvc_stage_hash"] == node.state.get_stage_hash()

    repo = aim.Repo(path=os.environ["AIM_TRACKING_URI"])
    for run_metrics_collection in repo.query_metrics(
        "metric.name == 'metrics.loss'"
    ).iter_runs():
        for metric in run_metrics_collection:
            params = metric.run[...]
            assert params["dvc_stage_hash"] == node.state.get_stage_hash()
            assert params["zntrack_node"] == "zntrack.examples.ParamsToMetrics"
            assert params["dvc_stage_name"] == "ParamsToMetrics"
            assert params["params"] == {"loss": 0}

            _, metric_values = metric.values.sparse_numpy()
            npt.assert_array_equal(metric_values, [0])
            assert metric.name == "metrics.loss"

    # make a git commit with all the changes
    repo = git.Repo()
    repo.git.add(".")
    repo.git.commit("-m", "test")
    node.state.plugins["AIMPlugin"].finalize()
