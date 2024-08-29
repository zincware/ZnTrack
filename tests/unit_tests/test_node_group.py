import zntrack

class MyNode(zntrack.Node):
    pass


def test_project_group(proj_path):
    proj = zntrack.Project()
    with proj.group():
        n = MyNode()
    
    assert n.state.group == ('Group1',)
    