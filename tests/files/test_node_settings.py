import json
import pathlib

import yaml

import zntrack.examples

CWD = pathlib.Path(__file__).parent.resolve()


def test_node_settings(proj_path):
    project = zntrack.Project()

    with project:
        _ = zntrack.examples.ParamsToOuts(
            params=1,
            always_changed=True,
        )
        _ = zntrack.examples.ParamsToOuts(
            params=2,
            always_changed=False,
        )

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "node_settings.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "node_settings.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "node_settings.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_node_settings(None)
