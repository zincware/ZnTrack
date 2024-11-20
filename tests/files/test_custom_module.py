import json
import pathlib

import yaml

import zntrack

CWD = pathlib.Path(__file__).parent.resolve()


class NodeFromCustomModule(zntrack.Node):
    _module_ = "zntrack.mymodule"

    def run(self):
        pass


def test__module_():
    proj_path = pathlib.Path.cwd()
    project = zntrack.Project()

    with project:
        NodeFromCustomModule()

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "custom_module.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "custom_module.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "custom_module.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()
