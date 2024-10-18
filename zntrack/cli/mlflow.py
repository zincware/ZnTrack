import dataclasses
import fnmatch
import json
import typing as t

import mlflow
import pandas as pd
import typer
import yaml
from dvc.api import DVCFileSystem
from mlflow.entities import Metric, Param, RunTag
from mlflow.tracking import MlflowClient
from mlflow.utils import mlflow_tags

from zntrack.cli.cli import app
from zntrack.config import ZNTRACK_OPTION, ZnTrackOptionEnum
from zntrack.from_rev import from_rev
from zntrack.node import Node

numeric = t.Union[int, float]
metrics_type = dict[str, t.Union[numeric, list[numeric]]]
params_type = dict[str, t.Any]


@dataclasses.dataclass
class MLFlowNodeData:
    metrics: metrics_type
    params: params_type
    tags: dict[str, str]

    def upload(self, nested: bool = False) -> None:
        metrics: list[Metric] = []
        params: list[Param] = []
        tags: list[RunTag] = []

        for key, value in self.metrics.items():
            if isinstance(value, list):
                for i, v in enumerate(value):
                    metrics.append(Metric(key=key, value=v, step=i, timestamp=i))
            else:
                metrics.append(Metric(key=key, value=value, step=0, timestamp=0))

        for key, value in self.params.items():
            params.append(Param(key=key, value=str(value)))

        for key, value in self.tags.items():
            tags.append(RunTag(key=key, value=value))

        with mlflow.start_run(nested=nested) as active_run:
            mlflow_client = MlflowClient()
            mlflow_client.log_batch(
                run_id=active_run.info.run_id, metrics=metrics, params=params, tags=tags
            )

    @classmethod
    def from_node(cls, node: Node) -> "MLFlowNodeData":
        metrics = {}
        params = {}
        tags = {}

        for field in dataclasses.fields(node):
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
                for key, value in getattr(node, field.name).items():
                    metrics[f"{field.name}.{key}"] = value
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS:
                df: pd.DataFrame = getattr(node, field.name)
                for column in df.columns:
                    metrics[f"{field.name}.{column}"] = df[column].values.tolist()
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
                params[field.name] = getattr(node, field.name)
            # TODO: metrics_path, plots_path and params_path are currently being ignored
            # TODO: dataclass deps are also ignored

        tags[mlflow_tags.MLFLOW_RUN_NAME] = node.name
        if node.state.rev is not None:
            tags[mlflow_tags.MLFLOW_GIT_COMMIT] = node.state.rev
        if node.state.remote is not None:
            tags[mlflow_tags.MLFLOW_GIT_REPO_URL] = node.state.remote
        if hasattr(node, "__run_note__"):
            tags[mlflow_tags.MLFLOW_RUN_NOTE] = node.__run_note__()

        tags["dvc_stage_hash"] = node.state.get_stage_hash()
        tags["zntrack_node"] = f"{node.__module__}.{node.__class__.__name__}"

        return cls(metrics=metrics, params=params, tags=tags)


@app.command()
def mlflow_sync(
    nodes: list[str] | None = typer.Argument(
        None, help="ZnTrack nodes to sync. You can use glob patterns. (default: all)"
    ),
    rev: str | None = typer.Option(None, help="Git revision to load nodes from."),
    remote: str | None = typer.Option(None, help="Git remote to load nodes from."),
    experiment: str | None = typer.Option(
        None, help="MLFlow experiment name.", envvar="MLFLOW_EXPERIMENT_NAME"
    ),
    uri: str | None = typer.Option(
        None, help="MLFlow tracking URI.", envvar="MLFLOW_TRACKING_URI"
    ),
    parent: str | None = typer.Option(
        None,
        help="Specify a parent run name to group all nodes under.",
        envvar="MLFLOW_PARENT_RUN_NAME",
    ),
    dry: bool = typer.Option(
        False, "--dry", help="Print the data that would be uploaded."
    ),
) -> None:
    """Synchronize ZnTrack nodes with MLFlow."""
    fs = DVCFileSystem(url=remote, rev=rev)
    with fs.open("dvc.yaml", "r") as f:
        config = yaml.safe_load(f)

    node_lst: list[Node] = []

    for stage_name in config["stages"]:
        if nodes is not None:
            if not any(fnmatch.fnmatch(stage_name, node) for node in nodes):
                continue
        node_lst.append(from_rev(name=stage_name, rev=rev, remote=remote))

    data = []

    for node in node_lst:
        data.append(MLFlowNodeData.from_node(node))

    if dry:
        for node_data in data:
            print(json.dumps(dataclasses.asdict(node_data), indent=2))
        return

    if uri is not None:
        mlflow.set_tracking_uri(uri)

    if experiment is not None:
        mlflow.set_experiment(experiment)

    if parent is not None:
        with mlflow.start_run(run_name=parent):
            for node_data in data:
                node_data.upload(nested=True)
    else:
        for node_data in data:
            node_data.upload()
