import pathlib
import typing as t

import git
import pytest

import zntrack.examples

# from zntrack.project import Experiment
# from zntrack.utils import config


class ZnNodesNode(zntrack.Node):
    """Used zn.nodes"""

    params: t.Any = zntrack.deps()
    result: t.Any = zntrack.outs()

    def run(self) -> None:
        self.result = self.params


@pytest.mark.xfail(reason="pending implementation")
@pytest.mark.parametrize("assert_before_exp", [True, False])
def test_WriteIO(tmp_path_2, assert_before_exp):
    """Test the WriteIO node."""
    with zntrack.Project() as project:
        node = zntrack.examples.ParamsToOuts(params="Hello World")

    project.run()
    # node.load()
    if assert_before_exp:
        assert node.outs == "Hello World"

    # write a non-tracked file using pathlib
    pathlib.Path("test.txt").write_text("Hello World")

    with project.create_experiment(name="exp1") as exp1:
        node.params = "Hello World"

    # check that the file is still there
    assert pathlib.Path("test.txt").read_text() == "Hello World"

    with project.create_experiment(name="exp2") as exp2:
        node.params = "Lorem Ipsum"

    assert exp1.name == "exp1"
    assert exp2.name == "exp2"

    assert project.experiments.keys() == {"exp1", "exp2"}

    # assert isinstance(project.experiments["exp1"], Experiment)

    project.run_exp()
    assert node.from_rev(rev="exp1").params == "Hello World"
    assert node.from_rev(rev="exp1").outs == "Hello World"

    assert node.from_rev(rev="exp2").params == "Lorem Ipsum"
    assert node.from_rev(rev="exp2").outs == "Lorem Ipsum"

    exp2.apply()
    assert (
        zntrack.from_rev("ParamsToOuts").params
        == zntrack.from_rev("ParamsToOuts", rev=exp2.name).params
    )
    exp1.apply()
    assert (
        zntrack.from_rev("ParamsToOuts").params
        == zntrack.from_rev("ParamsToOuts", rev=exp1.name).params
    )


@pytest.mark.xfail(reason="pending implementation")
@pytest.mark.parametrize("assert_before_exp", [True, False])
def test_WriteIO_no_name(tmp_path_2, assert_before_exp):
    """Test the WriteIO node."""
    with zntrack.Project() as project:
        node = zntrack.examples.ParamsToOuts(params="Hello World")

    project.run()
    # node.load()
    if assert_before_exp:
        assert node.outs == "Hello World"

    with project.create_experiment() as exp1:
        node.params = "Hello World"

    with project.create_experiment() as exp2:
        node.params = "Lorem Ipsum"

    project.run_exp()

    exp1.load()
    assert exp1.nodes["ParamsToOuts"].params == "Hello World"
    assert exp1.nodes["ParamsToOuts"].outs == "Hello World"

    assert exp1["ParamsToOuts"].params == "Hello World"
    assert exp1["ParamsToOuts"].outs == "Hello World"

    exp2.load()
    assert exp2.nodes["ParamsToOuts"].params == "Lorem Ipsum"
    assert exp2.nodes["ParamsToOuts"].outs == "Lorem Ipsum"

    assert exp2["ParamsToOuts"].params == "Lorem Ipsum"
    assert exp2["ParamsToOuts"].outs == "Lorem Ipsum"

    assert zntrack.from_rev("ParamsToOuts", rev=exp1.name).params == "Hello World"
    assert zntrack.from_rev("ParamsToOuts", rev=exp1.name).outs == "Hello World"

    assert zntrack.from_rev("ParamsToOuts", rev=exp2.name).params == "Lorem Ipsum"
    assert zntrack.from_rev("ParamsToOuts", rev=exp2.name).outs == "Lorem Ipsum"


def test_project_remove_graph(proj_path):
    with zntrack.Project() as project:
        node = zntrack.examples.ParamsToOuts(params="Hello World")
    project.run()

    assert node.outs == "Hello World"

    with zntrack.Project(remove_existing_graph=True) as project:
        node2 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum", name="node2")
    project.run()

    assert node2.outs == "Lorem Ipsum"


def test_project_repr_node(tmp_path_2):
    with zntrack.Project():
        node = zntrack.examples.ParamsToOuts(params="Hello World")
        print(node)


@pytest.mark.xfail(reason="pending implementation")
def test_automatic_node_names_False(tmp_path_2):
    with pytest.raises(zntrack.exceptions.DuplicateNodeNameError):
        with zntrack.Project(automatic_node_names=False):
            _ = zntrack.examples.ParamsToOuts(params="Hello World")
            _ = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
    with pytest.raises(zntrack.exceptions.DuplicateNodeNameError):
        with zntrack.Project(automatic_node_names=False):
            _ = zntrack.examples.ParamsToOuts(params="Hello World", name="NodeA")
            _ = zntrack.examples.ParamsToOuts(params="Lorem Ipsum", name="NodeA")


def test_automatic_node_names_default(tmp_path_2):
    with zntrack.Project(automatic_node_names=False):
        _ = zntrack.examples.ParamsToOuts(params="Hello World")
        _ = zntrack.examples.ParamsToOuts(params="Lorem Ipsum", name="WriteIO2")


@pytest.mark.xfail(reason="pending implementation")
def test_automatic_node_names_True(tmp_path_2):
    with zntrack.Project(automatic_node_names=True) as project:
        node = zntrack.examples.ParamsToOuts(params="Hello World")
        node2 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
        assert node.name == "ParamsToOuts"
        assert node2.name == "ParamsToOuts_1"
    project.run()

    with project:
        node3 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
        assert node3.name == "ParamsToOuts_2"

    project.run()

    assert node.name == "ParamsToOuts"
    assert node2.name == "ParamsToOuts_1"
    assert node3.name == "ParamsToOuts_2"

    project.run()
    # project.load()
    assert "ParamsToOuts" in project.nodes
    assert "ParamsToOuts_1" in project.nodes
    assert "ParamsToOuts_2" in project.nodes

    assert node.outs == "Hello World"
    assert node2.outs == "Lorem Ipsum"
    assert node3.outs == "Dolor Sit"


def test_group_nodes(proj_path):
    with zntrack.Project(automatic_node_names=True) as project:
        with project.group() as group_1:
            node_1 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
            node_2 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
        with project.group() as group_2:
            node_3 = zntrack.examples.ParamsToOuts(
                params="Amet Consectetur", name="Node01"
            )
            node_4 = zntrack.examples.ParamsToOuts(
                params="Adipiscing Elit", name="Node02"
            )
        with project.group("NamedGrp") as group_3:
            node_5 = zntrack.examples.ParamsToOuts(params="Sed Do")
            node_6 = zntrack.examples.ParamsToOuts(params="Eiusmod Tempor", name="Node03")

        node7 = zntrack.examples.ParamsToOuts(params="Hello World")
        node8 = zntrack.examples.ParamsToOuts(params="How are you?")
        node9 = zntrack.examples.ParamsToOuts(params="I'm fine, thanks!", name="Node04")

    project.repro()

    assert node_1.name == "Group1_ParamsToOuts"
    assert node_2.name == "Group1_ParamsToOuts_1"
    assert node_3.name == "Group2_Node01"
    assert node_4.name == "Group2_Node02"
    assert node_5.name == "NamedGrp_ParamsToOuts"
    assert node_6.name == "NamedGrp_Node03"
    assert node7.name == "ParamsToOuts"
    assert node8.name == "ParamsToOuts_1"
    assert node9.name == "Node04"

    assert group_1.names == ("Group1",)
    assert group_2.names == ("Group2",)
    assert group_3.names == ("NamedGrp",)

    # test nodes in groups
    assert node_1 in group_1
    assert node_2 in group_1
    assert node_3 not in group_1
    assert node_4 not in group_1
    assert len(group_1) == 2
    assert group_1.nwd == pathlib.Path("nodes", "Group1")
    assert node_3 in group_2
    assert node_4 in group_2
    assert node_5 in group_3
    assert node_6 in group_3

    for node in group_1.nodes:
        assert node.state.group == group_1

    for node in group_2.nodes:
        assert node.state.group == group_2

    for node in group_3.nodes:
        assert node.state.group == group_3

    # test node_names in project
    assert node_1.name in group_1
    assert node_2.name in group_1
    assert node_3.name in group_2
    assert node_4.name in group_2
    assert node_5.name in group_3
    assert node_6.name in group_3

    assert node_1.name not in group_2
    assert node_2.name not in group_2
    assert node_3.name not in group_1
    assert node_4.name not in group_1

    # test getitem with node name
    assert group_1[node_1.name] == node_1
    assert group_1[node_2.name] == node_2
    assert group_2[node_3.name] == node_3
    assert group_2[node_4.name] == node_4
    assert group_3[node_5.name] == node_5
    assert group_3[node_6.name] == node_6

    with pytest.raises(KeyError):
        group_1["NodeA"]

    # test iter group
    assert list(group_1) == [node_1, node_2]
    assert list(group_2) == [node_3, node_4]
    assert list(group_3) == [node_5, node_6]

    assert group_1.names == ("Group1",)
    assert group_2.names == ("Group2",)
    assert group_3.names == ("NamedGrp",)

    assert (
        zntrack.examples.ParamsToOuts.from_rev(name="NamedGrp_ParamsToOuts").params
        == "Sed Do"
    )


@pytest.mark.xfail(reason="pending implementation")
def test_build_certain_nodes(tmp_path_2):
    # TODO support passing groups to project.build
    with zntrack.Project(automatic_node_names=True) as project:
        node_1 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
        node_2 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
    project.build(nodes=[node_1, node_2])
    project.repro()

    assert zntrack.from_rev(node_1).outs == "Lorem Ipsum"
    assert zntrack.from_rev(node_2).outs == "Dolor Sit"

    node_1.params = "ABC"
    node_2.params = "DEF"

    project.build(nodes=[node_1])
    project.repro()

    assert zntrack.from_rev(node_1).outs == "ABC"
    assert zntrack.from_rev(node_2).outs == "Dolor Sit"

    project.run(nodes=[node_2])

    assert zntrack.from_rev(node_1).outs == "ABC"
    assert zntrack.from_rev(node_2).outs == "DEF"


@pytest.mark.xfail(reason="pending implementation")
def test_build_groups(tmp_path_2):
    with zntrack.Project(automatic_node_names=True) as project:
        with project.group() as group_1:
            node_1 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
            node_2 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
        with project.group() as group_2:
            node_3 = zntrack.examples.ParamsToOuts(params="Amet Consectetur")
            node_4 = zntrack.examples.ParamsToOuts(params="Adipiscing Elit")

    project.run(nodes=[group_1])

    assert zntrack.from_rev(node_1).outs == "Lorem Ipsum"
    assert zntrack.from_rev(node_2).outs == "Dolor Sit"

    with pytest.raises(ValueError):
        zntrack.from_rev(node_3)
    with pytest.raises(ValueError):
        zntrack.from_rev(node_4)

    node_2.params = "DEF"

    project.run(nodes=[group_2, node_2])

    assert zntrack.from_rev(node_1).outs == "Lorem Ipsum"

    assert zntrack.from_rev(node_2).outs == "DEF"
    assert zntrack.from_rev(node_3).outs == "Amet Consectetur"
    assert zntrack.from_rev(node_4).outs == "Adipiscing Elit"

    with pytest.raises(TypeError):
        project.run(nodes=42)

    with pytest.raises(ValueError):
        project.run(nodes=[42])

    # assert that the only directories in "nodes/" are "Group1" and "Group2"
    assert {path.name for path in (tmp_path_2 / "nodes").iterdir()} == {
        "Group1",
        "Group2",
    }


@pytest.mark.xfail(reason="pending implementation")
def test_groups_nwd(tmp_path_2):
    with zntrack.Project(automatic_node_names=True) as project:
        node_1 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
        with project.group():
            node_2 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
        with project.group("CustomGroup"):
            node_3 = zntrack.examples.ParamsToOuts(params="Adipiscing Elit")

    project.build()

    assert node_1.nwd == pathlib.Path("nodes", node_1.name)
    assert node_2.nwd == pathlib.Path(
        "nodes", "Group1", node_2.name.replace("Group1_", "")
    )
    assert node_3.nwd == pathlib.Path(
        "nodes", "CustomGroup", node_3.name.replace("CustomGroup_", "")
    )
    # now load the Nodes and assert as well

    # assert zntrack.from_rev(node_1).nwd == pathlib.Path("nodes", node_1.name)
    # assert zntrack.from_rev(node_2).nwd == pathlib.Path(
    #     "nodes", "Group1", node_2.name.replace("Group1_", "")
    # )
    # assert zntrack.from_rev(node_3).nwd == pathlib.Path(
    #     "nodes", "CustomGroup", node_3.name.replace("CustomGroup_", "")
    # )

    # with open(config.files.zntrack) as f:
    #     data = json.load(f)
    #     data[node_1.name]["nwd"]["value"] = "test"
    #     data[node_2.name].pop("nwd")

    # with open(config.files.zntrack, "w") as f:
    #     json.dump(data, f)

    # assert zntrack.from_rev(node_1).nwd == pathlib.Path("test")
    # assert zntrack.from_rev(node_2).nwd == pathlib.Path("nodes", node_2.name)
    # assert zntrack.from_rev(node_3).nwd == pathlib.Path(
    #     "nodes", "CustomGroup", node_3.name.replace("CustomGroup_", "")
    # )


@pytest.mark.xfail(reason="pending implementation")
def test_groups_nwd_zn_nodes_a(tmp_path_2):
    node = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
    with zntrack.Project(automatic_node_names=True) as project:
        node_1 = ZnNodesNode(node=node)
        with project.group():
            node_2 = ZnNodesNode(node=node)
        with project.group("CustomGroup"):
            node_3 = ZnNodesNode(node=node)

    assert node_1.name == "ZnNodesNode"
    assert node_1.node.name == "ZnNodesNode+node"

    assert node_2.name == "Group1_ZnNodesNode"
    assert node_2.node.name == "Group1_ZnNodesNode+node"

    assert node_3.name == "CustomGroup_ZnNodesNode"
    assert node_3.node.name == "CustomGroup_ZnNodesNode+node"

    project.run()

    assert zntrack.from_rev(node_1).nwd == pathlib.Path("nodes/ZnNodesNode")
    assert zntrack.from_rev(node_2).nwd == pathlib.Path("nodes", "Group1", "ZnNodesNode")
    assert zntrack.from_rev(node_3).nwd == pathlib.Path(
        "nodes", "CustomGroup", "ZnNodesNode"
    )

    project.load()
    assert node_1.result == "Lorem Ipsum"
    assert node_2.result == "Lorem Ipsum"
    assert node_3.result == "Lorem Ipsum"


@pytest.mark.xfail(reason="pending implementation")
def test_groups_nwd_zn_nodes_b(tmp_path_2):
    node = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
    with zntrack.Project(automatic_node_names=True) as project:
        with project.group():
            node_2 = ZnNodesNode(node=node)
        with project.group("CustomGroup"):
            node_3 = ZnNodesNode(node=node)

    project.run()

    assert zntrack.from_rev(node_2).nwd == pathlib.Path("nodes", "Group1", "ZnNodesNode")
    assert zntrack.from_rev(node_3).nwd == pathlib.Path(
        "nodes", "CustomGroup", "ZnNodesNode"
    )

    project.load()
    assert node_2.result == "Lorem Ipsum"
    assert node_3.result == "Lorem Ipsum"


def test_reopening_groups(proj_path):
    with zntrack.Project(automatic_node_names=True) as project:
        with project.group("AL0"):
            node_1 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
            node_2 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
            node_3 = zntrack.examples.ParamsToOuts(params="Amet Consectetur")
        with project.group("AL0"):
            node_4 = zntrack.examples.ParamsToOuts(params="Adipiscing Elit")

    project.run()

    assert node_1.nwd == pathlib.Path("nodes", "AL0", "ParamsToOuts")
    assert node_2.nwd == pathlib.Path("nodes", "AL0", "ParamsToOuts_1")
    assert node_3.nwd == pathlib.Path("nodes", "AL0", "ParamsToOuts_2")

    assert node_4.nwd == pathlib.Path("nodes", "AL0", "ParamsToOuts_3")


@pytest.mark.xfail(reason="pending implementation")
def test_nested_groups(proj_path):
    with zntrack.Project(automatic_node_names=True) as project:
        with project.group("AL0"):
            node_1 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
        with project.group("AL0", "CPU"):
            node_2 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
        with project.group("AL0", "GPU"):
            node_3 = zntrack.examples.ParamsToOuts(params="Amet Consectetur")

    project.run()
    project.load()

    assert node_1.nwd == pathlib.Path("nodes", "AL0", "ParamsToOuts")
    assert node_2.nwd == pathlib.Path("nodes", "AL0", "CPU", "ParamsToOuts")
    assert node_3.nwd == pathlib.Path("nodes", "AL0", "GPU", "ParamsToOuts")

    assert node_1.outs == "Lorem Ipsum"
    assert node_2.outs == "Dolor Sit"
    assert node_3.outs == "Amet Consectetur"


@pytest.mark.xfail(reason="pending implementation")
def test_nested_groups_direct_enter(proj_path):
    project = zntrack.Project(automatic_node_names=True)

    with project.group("AL0"):
        node_1 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
    with project.group("AL0", "CPU"):
        node_2 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
    with project.group("AL0", "GPU"):
        node_3 = zntrack.examples.ParamsToOuts(params="Amet Consectetur")

    project.run()
    project.load()

    assert node_1.nwd == pathlib.Path("nodes", "AL0", "ParamsToOuts")
    assert node_2.nwd == pathlib.Path("nodes", "AL0", "CPU", "ParamsToOuts")
    assert node_3.nwd == pathlib.Path("nodes", "AL0", "GPU", "ParamsToOuts")

    assert node_1.outs == "Lorem Ipsum"
    assert node_2.outs == "Dolor Sit"
    assert node_3.outs == "Amet Consectetur"


@pytest.mark.xfail(reason="pending implementation")
def test_group_dvc_outs(proj_path):
    project = zntrack.Project(automatic_node_names=True)

    with project.group("GRP1"):
        node = zntrack.examples.WriteDVCOuts(params="Hello World")

    project.run()

    assert node.outs == pathlib.Path("nodes", "GRP1", "WriteDVCOuts", "output.txt")
    assert zntrack.examples.WriteDVCOuts.from_rev(node.name).outs == pathlib.Path(
        "nodes", "GRP1", "WriteDVCOuts", "output.txt"
    )


@pytest.mark.xfail(reason="pending implementation")
def test_auto_remove(proj_path):
    with zntrack.Project(automatic_node_names=True) as project:
        n1 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
        n2 = zntrack.examples.ParamsToOuts(params="Dolor Sit")

    project.run()

    n1 = zntrack.examples.ParamsToOuts.from_rev(n1.name)
    n2 = zntrack.examples.ParamsToOuts.from_rev(n2.name)
    assert n1.outs == "Lorem Ipsum"
    assert n2.outs == "Dolor Sit"

    repo = git.Repo()
    repo.git.add(".")
    repo.index.commit("initial commit")

    with zntrack.Project(automatic_node_names=True) as project:
        n1 = zntrack.examples.ParamsToOuts(params="Hello World")

    project.run(auto_remove=True)

    n1 = zntrack.examples.ParamsToOuts.from_rev(n1.name)
    # with pytest.raises(zntrack.exceptions.NodeNotAvailableError):
    #     n2 = zntrack.examples.ParamsToOuts.from_rev(n2.name)


@pytest.mark.xfail(reason="pending implementation")
def test_magic_names(proj_path):
    node = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
    assert node.name == "ParamsToOuts"
    with pytest.raises(ValueError):
        project = zntrack.Project(magic_names=True, automatic_node_names=True)

    project = zntrack.Project(magic_names=True, automatic_node_names=False)
    with project:
        node01 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
        node02 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
        node03 = zntrack.examples.ParamsToOuts(params="Test01")
    assert node01.name == "node01"
    assert node02.name == "node02"
    assert node03.name == "node03"

    with project.group("Grp01"):
        node01 = zntrack.examples.ParamsToOuts(params="Lorem Ipsum")
        node02 = zntrack.examples.ParamsToOuts(params="Dolor Sit")
        grp_node03 = zntrack.examples.ParamsToOuts(params="Test02")

    assert node01.name == "Grp01_node01"
    assert node02.name == "Grp01_node02"
    assert grp_node03.name == "Grp01_grp_node03"

    project.run()

    assert zntrack.from_rev(node01.name).outs == "Lorem Ipsum"
    assert zntrack.from_rev(node02.name).outs == "Dolor Sit"
    assert zntrack.from_rev(node03.name).outs == "Test01"
    assert zntrack.from_rev(grp_node03.name).outs == "Test02"


def test_group_names(proj_path):
    project = zntrack.Project()
    with project.group() as grp1:
        pass
    with project.group() as grp2:
        pass
    with project.group("NamedGrp") as grp3:
        pass

    assert grp1.names == ("Group1",)
    assert grp2.names == ("Group2",)
    assert grp3.names == ("NamedGrp",)
