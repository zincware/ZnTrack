import zntrack.group


class MyNode(zntrack.Node):
    pass


def test_project_group(proj_path):
    proj = zntrack.Project()
    with proj.group() as grp:
        n = MyNode()

    assert isinstance(grp, zntrack.group.Group)
    assert grp.names == ("Group1",)
    assert n in grp
    assert n.state.group == grp
    assert len(grp) == 1
    assert n.name == "Group1_MyNode"
