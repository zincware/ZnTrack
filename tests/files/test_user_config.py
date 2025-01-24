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
    assert zntrack.config.ALWAYS_CACHE is False
    zntrack.config.ALWAYS_CACHE = True
    assert zntrack.config.ALWAYS_CACHE is True

    with zntrack.Project() as proj:
        node = MyNode()

    proj.repro()

    zntrack.config.ALWAYS_CACHE = False # reset to default value
    assert zntrack.config.ALWAYS_CACHE is False

    assert json.loads(
        (CWD / "zntrack_config" / "user_config.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "user_config.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "user_config.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()



if __name__ == "__main__":
    test_node("")
