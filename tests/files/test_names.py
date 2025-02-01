"""Test correct stage/node names."""

import json
import pathlib

import yaml

import zntrack.examples

CWD = pathlib.Path(__file__).parent.resolve()


def test_names(proj_path):
    project = zntrack.Project()

    with project:
        zntrack.examples.ParamsToMetrics(params={"loss": 0.01})
        zntrack.examples.ParamsToMetrics(params={"loss": 0.02})
        zntrack.examples.ParamsToMetrics(params={"loss": 0.03}, name="Thanasis")

    with project.group("grp"):
        zntrack.examples.ParamsToMetrics(params={"loss": 0.04})
        zntrack.examples.ParamsToMetrics(params={"loss": 0.05})
        zntrack.examples.ParamsToMetrics(params={"loss": 0.06}, name="Cydney")

    with project.group("grp", "subgrp"):
        zntrack.examples.ParamsToMetrics(params={"loss": 0.07})
        zntrack.examples.ParamsToMetrics(params={"loss": 0.08})
        zntrack.examples.ParamsToMetrics(params={"loss": 0.09}, name="Lorine")

    project.build()

    assert json.loads((CWD / "zntrack_config" / "names.json").read_text()) == json.loads(
        (proj_path / "zntrack.json").read_text()
    )
    assert yaml.safe_load(
        (CWD / "dvc_config" / "names.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "names.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()
