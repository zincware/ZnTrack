import dataclasses
from pathlib import Path

import pytest
import yaml

import zntrack


@dataclasses.dataclass
class SimpleThermostat:
    """Simple thermostat class"""


@dataclasses.dataclass
class ThermostatA:
    temperature: float


@dataclasses.dataclass
class ThermostatB:
    temperature: float


@dataclasses.dataclass
class ClassWithDepsAndParams:
    """Class with deps and params"""

    temperature: float

    config: list[Path | str] | Path | str = zntrack.params_path()
    files: list[Path | str] | Path | str = zntrack.deps_path()


class HasBase:
    """Base class for unsupported fields."""


@dataclasses.dataclass
class HasOuts(HasBase):
    val: str = zntrack.outs()


@dataclasses.dataclass
class HasMetrics(HasBase):
    val: str = zntrack.metrics()


@dataclasses.dataclass
class HasPlots(HasBase):
    val: str = zntrack.plots()


@dataclasses.dataclass
class HasDeps(HasBase):
    val: str = zntrack.deps()


@dataclasses.dataclass
class HasParams(HasBase):
    val: str = zntrack.params()


class HasIllegalDC(zntrack.Node):
    method: HasBase = zntrack.deps()


class MD(zntrack.Node):
    thermostat: ThermostatA | ThermostatB | SimpleThermostat | ClassWithDepsAndParams = (
        zntrack.deps()
    )

    result: str = zntrack.outs()

    def run(self):
        self.result = self.thermostat.__class__.__name__


def test_switch_deps_class_keep_params(proj_path):
    """Test that changing the class triggers a DVC run."""
    proj = zntrack.Project()

    thermostat_a = ThermostatA(temperature=10)
    thermostat_b = ThermostatB(temperature=5)
    thermostat_c = SimpleThermostat()

    with proj:
        md = MD(thermostat=thermostat_a)

    proj.repro()
    assert md.from_rev().result == "ThermostatA"

    with proj:
        md.thermostat = thermostat_b

    proj.repro()
    assert md.from_rev().result == "ThermostatB"

    with proj:
        md.thermostat = thermostat_c

    proj.repro()
    assert md.from_rev().result == "SimpleThermostat"


def test_dc_deps_params_files(proj_path):
    config_file = Path("config.yaml")
    config_file.write_text(yaml.dump({"value": 10}))
    deps_file = Path("file.txt")
    deps_file.write_text("test")
    project = zntrack.Project()

    instance = ClassWithDepsAndParams(
        temperature=10,
        config=[config_file],
        files=deps_file,
    )
    with project:
        md = MD(thermostat=instance)

    project.repro()

    node = md.from_rev()
    assert isinstance(node.thermostat, ClassWithDepsAndParams)
    assert node.thermostat.temperature == 10
    assert node.thermostat.config == [config_file]
    assert node.thermostat.files == deps_file
    assert node.result == "ClassWithDepsAndParams"


@pytest.mark.parametrize(
    "node_class",
    [
        HasDeps,
        HasParams,
    ],
)
def test_dc_with_wrong_field_init(node_class):
    """Test that dataclass with wrong field raises an error."""
    project = zntrack.Project()
    instance = node_class(val="test")
    with project:
        HasIllegalDC(method=instance)
    with pytest.raises(TypeError):
        project.build()


@pytest.mark.parametrize(
    "node_class",
    [
        HasOuts,
        HasMetrics,
        HasPlots,
    ],
)
def test_dc_with_wrong_field_no_init(node_class):
    """Test that dataclass with wrong field raises an error."""
    project = zntrack.Project()
    instance = node_class()
    with project:
        HasIllegalDC(method=instance)
    with pytest.raises(TypeError):
        project.build()


if __name__ == "__main__":
    test_switch_deps_class_keep_params("")
