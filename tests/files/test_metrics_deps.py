import json
import pathlib

import yaml

import zntrack.examples

CWD = pathlib.Path(__file__).parent.resolve()


def test_metrics_as_deps(proj_path):
    project = zntrack.Project()

    with project:
        metrics_node = zntrack.examples.ParamsToMetrics(params={"loss": 0.01})

        zntrack.examples.DepsToMetrics(deps=metrics_node.metrics)
        zntrack.examples.DepsToMetrics(deps=metrics_node.params)

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "metrics_deps.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "metrics_deps.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "metrics_deps.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()
