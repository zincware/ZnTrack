import zntrack.examples
import os
import pathlib
import json
import yaml

IMPORT_URL_FILE = "https://raw.githubusercontent.com/PythonFZ/zntrack-examples/refs/heads/main/LICENSE"

CWD = pathlib.Path(__file__).parent.resolve()


def test_add_url(proj_path) -> None:
    project = zntrack.Project()
    file = zntrack.add(IMPORT_URL_FILE, "LICENSE")

    with project:
        zntrack.examples.ReadFile(path=file)

    project.build()

    assert json.loads((CWD / "zntrack_config" / "add.json").read_text()) == json.loads(
        (proj_path / "zntrack.json").read_text()
    )
    assert yaml.safe_load(
        (CWD / "dvc_config" / "add.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "add.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()

    assert (proj_path / "LICENSE.dvc").exists()

