import dataclasses
import zntrack

@dataclasses.dataclass
class Langevin:
    """Langevin dynamics class"""

    def get_thermostat(self):
        return "Langevin thermostat"


@dataclasses.dataclass
class Berendsen:
    """Berendsen thermostat class"""

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
        md = MD(thermostat=thermostat)
        
    project.repro()
    assert md.from_rev().result == "Langevin thermostat"
