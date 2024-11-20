import dataclasses

import zntrack


@dataclasses.dataclass
class SimpleThermostat:
    """Simple thermostat class"""


@dataclasses.dataclass
class ThermostatA:
    temperature: float = zntrack.params()


@dataclasses.dataclass
class ThermostatB:
    temperature: float = zntrack.params()


class MD(zntrack.Node):
    thermostat: ThermostatA | ThermostatB | SimpleThermostat = zntrack.deps()

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


if __name__ == "__main__":
    test_switch_deps_class_keep_params("")
