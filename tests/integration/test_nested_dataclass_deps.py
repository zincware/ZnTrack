import dataclasses
import zntrack

@dataclasses.dataclass
class Langevin:
    """Langevin dynamics class"""
    friction: float = 0.1

    def get_thermostat(self):
        return f"Langevin thermostat '{self.friction}'"


@dataclasses.dataclass
class Berendsen:
    """Berendsen thermostat class"""
    time: float = 0.5

    def get_thermostat(self):
        return f"Berendsen thermostat '{self.time}'"
    
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
    assert md.from_rev().result == "Langevin thermostat '0.1'"

    md.thermostat.method = Langevin(friction=0.2)
    project.repro()
    
    assert md.from_rev().result == "Langevin thermostat '0.2'"

    md.thermostat.method = Berendsen(time=1.0)
    project.repro()
    
    assert md.from_rev().result == "Berendsen thermostat '1.0'"
