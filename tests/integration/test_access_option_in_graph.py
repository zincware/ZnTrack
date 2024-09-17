import zntrack.examples


def test_connect_node_names(proj_path):
    with zntrack.Project() as proj:
        a = zntrack.examples.ParamsToOuts(params=10, name="A")
        assert a.name == "A"
        b = zntrack.examples.ParamsToOuts(params=20, name=f"con_{a.name}")
        assert b.name == "con_A"
    proj.repro()

    assert a.name == "A"
    assert b.name == "con_A"


def test_connect_node_names_automatic_names(proj_path):
    with zntrack.Project() as proj:
        a = zntrack.examples.ParamsToOuts(params=10)
        assert a.name == "ParamsToOuts"
        b = zntrack.examples.ParamsToOuts(params=20, name=f"con_{a.name}")
        assert b.name == "con_ParamsToOuts"

    proj.repro()

    assert a.name == "ParamsToOuts"
    assert b.name == "con_ParamsToOuts"


def test_connect_nodes_in_grp(proj_path):
    proj = zntrack.Project()
    with proj.group("A", "B"):
        a = zntrack.examples.ParamsToOuts(params=10)
        assert a.name == "A_B_ParamsToOuts"
        b = zntrack.examples.ParamsToOuts(params=20, name=f"con_{a.name}")
        assert b.name == "con_A_B_ParamsToOuts"

    proj.repro()

    assert a.name == "A_B_ParamsToOuts"
    assert b.name == "con_A_B_ParamsToOuts"
