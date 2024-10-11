import fnmatch
import json
import os
import pathlib
import uuid

import mlflow
import pandas as pd
import tqdm
import typer
import yaml
from dvc.api import DVCFileSystem

from zntrack.cli.cli import app

# TODO dry option without uploading to show the selected nodes and everything that would be uploaded


@app.command()
def mlflow_sync(
    nodes: list[str] | None = None,
    rev: str | None = None,
    remote: str | None = None,
    experiment: str | None = None,
    uri: str | None = None,
    parent: str | None = None,
) -> None:
    """Upload artifacts to MLflow."""
    fs = DVCFileSystem(url=remote, rev=rev)
    with fs.open("dvc.yaml", "r") as f:
        config = yaml.safe_load(f)

    metrics: dict = {}
    # metrics is a dict of style {stage_name: {metric_name: metric_value}}

    for stage_name, stage_config in config["stages"].items():
        # check if stage_name fits glob pattern in nodes
        if nodes is not None:
            if not any(fnmatch.fnmatch(stage_name, node) for node in nodes):
                continue
        if "metrics" in stage_config:
            for metric_config in stage_config["metrics"]:
                if isinstance(metric_config, dict):
                    path = next(iter(metric_config))
                else:
                    path = metric_config

                with fs.open(path, "r") as f:
                    content = json.load(f)

                prefix = pathlib.Path(path).stem
                content = {f"{prefix}.{k}": v for k, v in content.items()}
                # filter keys that are not int/float
                content = {
                    k: v for k, v in content.items() if isinstance(v, (int, float))
                }
                # TODO: if any of the keys are already used - use full file paths
                if stage_name not in metrics:
                    metrics[stage_name] = content
                else:
                    metrics[stage_name].update(content)
        if "outs" in stage_config:  # TODO: plots key
            for outs_config in stage_config["outs"]:
                if isinstance(outs_config, dict):
                    path = next(iter(outs_config))
                else:
                    path = outs_config

                if path.endswith(".csv"):  # only way right now to find plots
                    with fs.open(path, "r") as f:
                        content = pd.read_csv(f, index_col=0)
                    prefix = pathlib.Path(path).stem
                    content = {
                        f"{prefix}.{k}": v.values.tolist() for k, v in content.items()
                    }
                    if stage_name not in metrics:
                        metrics[stage_name] = content
                    else:
                        metrics[stage_name].update(content)

    if len(metrics) == 0:
        typer.echo("No metrics found.")
        return

    # upload to mlflow
    uri = os.getenv("MLFLOW_URI", uri)
    if uri is None:
        uri = "http://localhost:5000"
    mlflow.set_tracking_uri(uri)
    experiment_name = experiment or uuid.uuid4().hex
    mlflow.set_experiment(experiment_name)
    if parent is not None:
        mlflow.start_run(run_name=parent)
    for stage_name, stage_metrics in tqdm.tqdm(metrics.items()):
        with mlflow.start_run(run_name=stage_name, nested=True):
            for metric_name, metric_value in stage_metrics.items():
                if isinstance(metric_value, list):
                    for i, value in enumerate(metric_value):
                        mlflow.log_metric(metric_name, value, step=i)
                else:
                    mlflow.log_metric(metric_name, metric_value)

    if parent is not None:
        mlflow.end_run()

    typer.echo(f"Uploaded metrics to MLflow experiment '{experiment_name}'")
