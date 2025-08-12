"""Test params such as always_changed, ..."""

import json
import pathlib

import yaml

import zntrack

CWD = pathlib.Path(__file__).parent.resolve()


class MyNode(zntrack.Node):
    """Some Node."""

    def run(self) -> None:
        pass


def test_node(proj_path):
    with zntrack.Project() as proj:
        MyNode(name="some-node", always_changed=True)

    proj.repro()

    assert json.loads(
        (CWD / "zntrack_config" / "meta_params.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "meta_params.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "meta_params.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_node("")
