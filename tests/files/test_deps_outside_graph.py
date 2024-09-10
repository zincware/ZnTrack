import zntrack


class Thermostat(zntrack.Node):
    temperature: float = zntrack.params()


class MD(zntrack.Node):
    thermostat: Thermostat = zntrack.deps()
    steps: int = zntrack.params()


def test_deps_outside_graph(proj_path):
    thermostat = Thermostat(temperature=300)

    with zntrack.Project() as project:
        md = MD(thermostat=thermostat, steps=100)

    project.build()

    assert md.name == "MD"


if __name__ == "__main__":
    test_deps_outside_graph(None)
