import json
import os
import subprocess

import pytest

import zntrack

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
def use_aim_plugin():
    os.environ[
        "ZNTRACK_PLUGINS"
    ] = "zntrack.plugins.dvc_plugin.DVCPlugin,zntrack.plugins.aim_plugin.AIMPlugin"
    yield
    del os.environ["ZNTRACK_PLUGINS"]


@pytest.mark.skipif(aim is None, reason="Aim is not installed.")
def test_aim_metrics(proj_path, use_aim_plugin):
    subprocess.run(["aim", "init"], cwd=proj_path, check=True)

    with zntrack.Project() as proj:
        node = MetricsNode(user="Max", age=42)

    proj.build()

    subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)

    with open(node.nwd / "data.json") as f:
        metrics = json.load(f)

    assert metrics == {"age": 42}

    run = node.state.plugins["AIMPlugin"].get_aim_run()
    assert run["dvc_stage_hash"] == node.state.get_stage_hash()

    repo = aim.Repo(path=proj_path.as_posix())
    for run_metrics_collection in repo.query_metrics(
        "metric.name == 'data.age'"
    ).iter_runs():
        for metric in run_metrics_collection:
            params = metric.run[...]
            assert params["dvc_stage_hash"] == node.state.get_stage_hash()
            assert params["age"] == 42
            assert params["user"] == "Max"
            _, metric_values = metric.values.sparse_numpy()
            assert metric_values == [42]
            assert metric.name == "data.age"
