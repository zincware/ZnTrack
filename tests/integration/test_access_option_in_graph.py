import zntrack.examples


def test_connect_node_names(proj_path):
    with zntrack.Project() as proj:
        a = zntrack.examples.ParamsToOuts(params=10, name="A")
        b = zntrack.examples.ParamsToOuts(params=20, name=f"con_{a.name}")
    proj.build()

    assert a.name == "A"
    assert b.name == "con_A"


def test_connect_node_names_automatic_names(proj_path):
    with zntrack.Project() as proj:
        a = zntrack.examples.ParamsToOuts(params=10)
        b = zntrack.examples.ParamsToOuts(params=20, name=f"con_{a.name}")
    proj.build()

    assert a.name == "ParamsToOuts"
    assert b.name == "con_ParamsToOuts"
