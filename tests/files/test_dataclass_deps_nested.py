import dataclasses
import json
import pathlib

import yaml

import zntrack

CWD = pathlib.Path(__file__).parent.resolve()


@dataclasses.dataclass
class Langevin:
    """Langevin dynamics class"""

    friction: float = 0.1

    def get_thermostat(self):
        return "Langevin thermostat"


@dataclasses.dataclass
class Berendsen:
    """Berendsen thermostat class"""

    time: float = 0.5

    def get_thermostat(self):
        return "Berendsen thermostat"


@dataclasses.dataclass
class Thermostat:
    temperature: float
    method: Berendsen | Langevin


class MD(zntrack.Node):
    thermostat: Thermostat = zntrack.deps()
    result: str = zntrack.outs()

    def run(self):
        self.result = self.thermostat.method.get_thermostat()


def test_nested_dc_deps(proj_path):
    project = zntrack.Project()
    thermostat = Thermostat(temperature=300, method=Langevin())

    with project:
        _ = MD(thermostat=thermostat)

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "dataclass_deps_nested.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "dataclass_deps_nested.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "dataclass_deps_nested.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_nested_dc_deps(pathlib.Path.cwd())
