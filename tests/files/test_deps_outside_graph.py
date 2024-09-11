import dataclasses

import zntrack


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


if __name__ == "__main__":
    test_deps_outside_graph(None)
