import zntrack


class Thermostat(zntrack.Node):
    temperature: float = zntrack.params()


class MD(zntrack.Node):
    thermostat: Thermostat = zntrack.deps()
    steps: int = zntrack.params()


def test_deps_outside_graph(proj_path):
    thermostat = Thermostat(temperature=300)

    with zntrack.Project() as project:
        # in the main branch, the setter of the thermostat
        #  is creating a deepcopy of the thermostat and updating its name
        md = MD(thermostat=thermostat, steps=100)

    project.build()

    # TODO: the node name changes with every node the thermostat would be attached to
    #  it might be better if it is None!
    # TODO: assert that node.name when setting can not include a "+" character
    # The thermostat does not appear in the dvc.yaml, but only in `params:MD+thermostat`
    # how to handle deps going into the thermostat node?

    assert thermostat.name == "MD+thermostat"
    assert md.name == "MD"
    assert md.thermostat.name == "MD+thermostat"


if __name__ == "__main__":
    test_deps_outside_graph(None)
