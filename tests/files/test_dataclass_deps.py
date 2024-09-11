import dataclasses
import json
import pathlib

import yaml

import zntrack

CWD = pathlib.Path(__file__).parent.resolve()


@dataclasses.dataclass
class Thermostat:
    temperature: float


class MD(zntrack.Node):
    thermostat: Thermostat = zntrack.deps()
    steps: int = zntrack.params()


def test_deps_outside_graph(proj_path):
    thermostat = Thermostat(temperature=300)

    with zntrack.Project() as project:
        md = MD(thermostat=thermostat, steps=100)

    project.build()

    # TODO: lists / dicts / tuples
    assert md.name == "MD"

    node = md.from_rev()
    assert node.thermostat.temperature == thermostat.temperature

    assert json.loads(
        (CWD / "zntrack_config" / "dataclass_deps.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "dataclass_deps.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "dataclass_deps.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_deps_outside_graph(None)
