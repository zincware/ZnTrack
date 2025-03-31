import json
import pathlib

import yaml

import zntrack
import zntrack.group

CWD = pathlib.Path(__file__).parent.resolve()


class MyNode(zntrack.Node):
    parameter: int = zntrack.params()

    def run(self) -> None:
        pass


def test_group_nodes(proj_path):
    project = zntrack.Project()

    with project:
        a = MyNode(parameter=1)

    with project.group("Grp") as grp:
        b = MyNode(parameter=2)
        c = MyNode(parameter=3)
        d = MyNode(parameter=4)

    assert b in grp

    with project.group("Grp", "B") as grp_b:
        e = MyNode(parameter=5)

    project.build()

    assert a.state.group is None
    assert isinstance(b.state.group, zntrack.group.Group)
    assert b.state.group.names == ("Grp",)

    assert b in b.state.group
    assert c in b.state.group
    assert d in b.state.group

    assert len(b.state.group) == 3

    assert b.state.group == c.state.group == d.state.group == grp
    assert e.state.group == grp_b

    assert len(e.state.group) == 1

    assert a not in b.state.group

    assert a.name == "MyNode"
    assert b.name == "Grp_MyNode"
    assert c.name == "Grp_MyNode_1"
    assert d.name == "Grp_MyNode_2"

    assert json.loads((CWD / "zntrack_config" / "groups.json").read_text()) == json.loads(
        (proj_path / "zntrack.json").read_text()
    )
    assert yaml.safe_load(
        (CWD / "dvc_config" / "groups.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "groups.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_group_nodes("")
