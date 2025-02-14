import dataclasses
import os
import pathlib
import uuid

import git
import mlflow
import pandas as pd
import pytest
import yaml
from mlflow.utils import mlflow_tags

import zntrack.examples


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

    def __run_note__(self) -> str:
        return f"""
This is the MD Node from rev {self.state.rev}.

Run it via `MD(t=T1(temperature=1))`

within

```python
with zntrack.Project() as proj:
    md = MD(t=T1(temperature=1))
proj.repro()
```
"""


class RangePlotter(zntrack.Node):
    start: int = zntrack.params()
    stop: int = zntrack.params()

    plots: pd.DataFrame = zntrack.plots(y="range")

    def run(self):
        self.plots = pd.DataFrame({"idx": list(range(self.start, self.stop))})


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
    assert run.data.tags["zntrack_node"] == "zntrack.examples.nodes.ParamsToMetrics"

    # assert metrics
    assert run.data.metrics == {"metrics.loss": 0.0}

    # make a git commit with all the changes
    proj.finalize(msg="test")
    repo = git.Repo()

    run = mlflow.get_run(child_run_id)  # need to query the run again

    assert run.data.tags["git_commit_message"] == "test"
    assert run.data.tags["git_commit_hash"] == repo.head.commit.hexsha


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
    assert run.data.tags["git_commit_hash"] == repo.head.commit.hexsha


@pytest.mark.parametrize("skip_cached", [True, False])
def test_multiple_nodes(mlflow_proj_path, skip_cached):
    with zntrack.Project() as proj:
        a = zntrack.examples.ParamsToOuts(params=3)
        b = zntrack.examples.ParamsToOuts(params=7)
        c = zntrack.examples.SumNodeAttributesToMetrics(inputs=[a.outs, b.outs], shift=0)

    proj.repro()

    assert c.metrics == {"value": 10.0}

    with a.state.plugins["MLFlowPlugin"]:
        mlflow.get_run(a.state.plugins["MLFlowPlugin"].child_run_id)

    with b.state.plugins["MLFlowPlugin"]:
        b_run = mlflow.get_run(b.state.plugins["MLFlowPlugin"].child_run_id)

    with c.state.plugins["MLFlowPlugin"]:
        c_run = mlflow.get_run(c.state.plugins["MLFlowPlugin"].child_run_id)

    assert c_run.data.metrics == {"metrics.value": 10.0}

    proj.finalize(msg="exp1", skip_cached=skip_cached, update_run_names=not skip_cached)
    repo = git.Repo()

    a.params = 5
    proj.repro()

    proj.finalize(msg="exp2", skip_cached=skip_cached, update_run_names=not skip_cached)
    repo = git.Repo()

    # find all runs with `git_commit_hash` == repo.head.commit.hexsha
    runs = mlflow.search_runs(
        filter_string=f"tags.git_commit_hash = '{repo.head.commit.hexsha}'"
    )
    if skip_cached:
        assert len(runs) == 3
    else:
        assert len(runs) == 4

    a_run_2 = mlflow.search_runs(
        filter_string=(
            f"tags.git_commit_hash = '{repo.head.commit.hexsha}' "
            f"and tags.dvc_stage_name = '{a.name}'"
        ),
        output_format="list",
    )
    assert len(a_run_2) == 1
    a_run_2 = a_run_2[0]

    b_run_2 = mlflow.search_runs(
        filter_string=(
            f"tags.git_commit_hash = '{repo.head.commit.hexsha}'"
            f" and tags.dvc_stage_name = '{b.name}'"
        ),
        output_format="list",
    )
    if skip_cached:
        assert len(b_run_2) == 0
    else:
        assert len(b_run_2) == 1
        b_run_2 = b_run_2[0]
        assert b_run_2.data.tags["original_run_id"] == b_run.info.run_id
        # original runs will not be updated with a new name to
        # indicate that they are cached
        assert b_run_2.data.tags[mlflow_tags.MLFLOW_RUN_NAME] == "ParamsToOuts_1"

    c_run_2 = mlflow.search_runs(
        filter_string=(
            f"tags.git_commit_hash = '{repo.head.commit.hexsha}'"
            f" and tags.dvc_stage_name = '{c.name}'"
        ),
        output_format="list",
    )
    assert len(c_run_2) == 1
    c_run_2 = c_run_2[0]

    assert "original_run_id" not in a_run_2.data.tags
    assert "original_run_id" not in c_run_2.data.tags

    if skip_cached:
        assert a_run_2.data.tags[mlflow_tags.MLFLOW_RUN_NAME] == "ParamsToOuts"
        assert (
            c_run_2.data.tags[mlflow_tags.MLFLOW_RUN_NAME] == "SumNodeAttributesToMetrics"
        )
    else:
        assert a_run_2.data.tags[mlflow_tags.MLFLOW_RUN_NAME] == "exp2:ParamsToOuts"
        assert (
            c_run_2.data.tags[mlflow_tags.MLFLOW_RUN_NAME]
            == "exp2:SumNodeAttributesToMetrics"
        )

    assert c_run_2.data.metrics == {"metrics.value": 12.0}


def test_project_tags(mlflow_proj_path):
    with zntrack.Project(tags={"lorem": "ipsum", "hello": "world"}) as proj:
        a = zntrack.examples.ParamsToOuts(params=3)
        b = zntrack.examples.ParamsToOuts(params=7)
        c = zntrack.examples.SumNodeAttributesToMetrics(inputs=[a.outs, b.outs], shift=0)

    proj.repro()

    with a.state.plugins["MLFlowPlugin"]:
        a_run = mlflow.get_run(a.state.plugins["MLFlowPlugin"].child_run_id)
        parent_run = mlflow.get_run(a.state.plugins["MLFlowPlugin"].parent_run_id)

    with b.state.plugins["MLFlowPlugin"]:
        b_run = mlflow.get_run(b.state.plugins["MLFlowPlugin"].child_run_id)

    with c.state.plugins["MLFlowPlugin"]:
        c_run = mlflow.get_run(c.state.plugins["MLFlowPlugin"].child_run_id)

    assert a_run.data.tags["lorem"] == "ipsum"
    assert a_run.data.tags["hello"] == "world"

    assert b_run.data.tags["lorem"] == "ipsum"
    assert b_run.data.tags["hello"] == "world"

    assert c_run.data.tags["lorem"] == "ipsum"
    assert c_run.data.tags["hello"] == "world"

    assert parent_run.data.tags["lorem"] == "ipsum"
    assert parent_run.data.tags["hello"] == "world"


def test_dataclass_deps(mlflow_proj_path):
    t1 = T1(temperature=1)
    t2 = T2(temperature=1)

    with zntrack.Project() as proj:
        md = MD(t=t1)

    proj.repro()

    with md.state.plugins["MLFlowPlugin"]:
        run = mlflow.get_run(md.state.plugins["MLFlowPlugin"].child_run_id)

    assert (
        run.data.params["t"] == "[{'temperature': 1, '_cls': 'test_plugins_mlflow.T1'}]"
    )

    proj.finalize(msg="run1 exp.")
    git.Repo()

    mdx = MD.from_rev()
    assert mdx.__run_note__() != ""
    with mdx.state.plugins["MLFlowPlugin"]:
        run = mlflow.get_run(mdx.state.plugins["MLFlowPlugin"].child_run_id)
    assert run.data.tags[mlflow_tags.MLFLOW_RUN_NAME] == "run1:MD"

    md.t = t2
    proj.repro()

    md = MD.from_rev()

    with md.state.plugins["MLFlowPlugin"]:
        run = mlflow.get_run(md.state.plugins["MLFlowPlugin"].child_run_id)

    assert (
        run.data.params["t"] == "[{'temperature': 1, '_cls': 'test_plugins_mlflow.T2'}]"
    )

    proj.finalize(msg="run2 exp.")

    mdx = MD.from_rev()
    with mdx.state.plugins["MLFlowPlugin"]:
        run = mlflow.get_run(mdx.state.plugins["MLFlowPlugin"].child_run_id)
    assert run.data.tags[mlflow_tags.MLFLOW_RUN_NAME] == "run2:MD"

    with zntrack.Project() as proj:
        md = MD(t=[t1, t2])
    proj.repro()

    md = MD.from_rev()

    with md.state.plugins["MLFlowPlugin"]:
        run = mlflow.get_run(md.state.plugins["MLFlowPlugin"].child_run_id)

    assert run.data.params["t"] == (
        "[{'temperature': 1, '_cls': 'test_plugins_mlflow.T1'},"
        " {'temperature': 1, '_cls': 'test_plugins_mlflow.T2'}]"
    )

    md = zntrack.from_rev(md.name)
    assert hasattr(md, "__run_note__")
    assert md.__run_note__() != ""
    # assert run.data.tags[mlflow_tags.MLFLOW_RUN_NAME] == "run2:MD"
