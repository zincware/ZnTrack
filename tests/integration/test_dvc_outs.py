import pathlib
import typing

import zntrack.examples


class SingleNode(zntrack.Node):
    path1: pathlib.Path = zntrack.outs_path()

    def run(self):
        self.path1.write_text("")


class SingleNodeDefaultNWD(zntrack.Node):
    path1: pathlib.Path = zntrack.outs_path(zntrack.nwd / "test.json")

    def run(self):
        self.path1.write_text("")


class SingleNodeListOut(zntrack.Node):
    paths: typing.List[pathlib.Path] | typing.Tuple[pathlib.Path] = zntrack.outs_path()

    def run(self):
        for path in self.paths:
            path.write_text("Lorem Ipsum")


class AssertTempPath(zntrack.Node):
    path1: pathlib.Path = zntrack.outs_path(zntrack.nwd / "test.json")

    def run(self):
        with self.state.use_tmp_path():
            assert self.state.tmp_path is None
            assert self.name == "AssertTempPath"
            assert self.path1 == pathlib.Path("nodes", self.name, "test.json"), self.path1
            self.path1.write_text("lorem ipsum")


def test_run_temp_path(proj_path):
    project = zntrack.Project()
    with project:
        AssertTempPath()
    project.repro()


def test_load_dvc_outs(proj_path):
    with zntrack.Project() as proj:
        node = SingleNode(path1=pathlib.Path("test.json"), name="1500")

    proj.build()

    # node = node.from_rev(name="1500")
    assert node.path1 == pathlib.Path("test.json")

    assert SingleNode.from_rev(name="1500").path1 == pathlib.Path("test.json")


def test_multiple_outs(proj_path):
    with zntrack.Project() as proj:
        SingleNodeListOut(paths=[pathlib.Path("test_1.txt"), pathlib.Path("test_2.txt")])
    proj.build()
    proj.run()

    assert pathlib.Path("test_1.txt").read_text() == "Lorem Ipsum"
    assert pathlib.Path("test_2.txt").read_text() == "Lorem Ipsum"
    assert SingleNodeListOut.from_rev().paths == [
        pathlib.Path("test_1.txt"),
        pathlib.Path("test_2.txt"),
    ]


def test_multiple_outs_tuple(proj_path):
    with zntrack.Project() as proj:
        SingleNodeListOut(paths=(pathlib.Path("test_1.txt"), pathlib.Path("test_2.txt")))
    proj.build()
    proj.run()

    assert pathlib.Path("test_1.txt").read_text() == "Lorem Ipsum"
    assert pathlib.Path("test_2.txt").read_text() == "Lorem Ipsum"
    assert SingleNodeListOut.from_rev().paths == [
        pathlib.Path("test_1.txt"),
        pathlib.Path("test_2.txt"),
    ]


class SingleNodeInNodeDir(zntrack.Node):
    path: pathlib.Path | list[pathlib.Path | str] = zntrack.outs_path(
        zntrack.nwd / "test.json"
    )

    def run(self):
        self.nwd.mkdir(parents=True, exist_ok=True)
        if isinstance(self.path, list):
            [pathlib.Path(x).touch() for x in self.path]
        else:
            self.path.write_text("")


def test_SingleNodeInNodeDir(proj_path):
    with zntrack.Project() as proj:
        node = SingleNodeInNodeDir()
    proj.build()
    proj.run()

    assert node.path == pathlib.Path("nodes", "SingleNodeInNodeDir", "test.json")
    assert node.path.exists()

    result = SingleNodeInNodeDir.from_rev()
    assert result.path == pathlib.Path("nodes", "SingleNodeInNodeDir", "test.json")
    assert result.path.exists()


def test_SingleNodeInNodeDirMulti(proj_path):
    with zntrack.Project() as proj:
        node = SingleNodeInNodeDir(
            path=[zntrack.nwd / "test.json", "file.txt"], name="TestNode"
        )
    proj.build()
    proj.run()

    assert node.path == [pathlib.Path("nodes", "TestNode", "test.json"), "file.txt"]
    assert all(pathlib.Path(x).exists() for x in node.path)

    result = SingleNodeInNodeDir.from_rev(name="TestNode")
    assert result.path == [pathlib.Path("nodes", "TestNode", "test.json"), "file.txt"]
    assert all(pathlib.Path(x).exists() for x in result.path)


def test_SingleNodeDefaultNWD(proj_path):
    with zntrack.Project() as proj:
        n1 = SingleNodeDefaultNWD(name="SampleNode")
        n2 = SingleNodeDefaultNWD()
    proj.build()
    proj.run()

    assert n1.path1 == pathlib.Path("nodes", "SampleNode", "test.json")
    assert n2.path1 == pathlib.Path("nodes", "SingleNodeDefaultNWD", "test.json")

    assert SingleNodeDefaultNWD.from_rev().path1 == pathlib.Path(
        "nodes", "SingleNodeDefaultNWD", "test.json"
    )
    assert SingleNodeDefaultNWD.from_rev(name="SampleNode").path1 == pathlib.Path(
        "nodes", "SampleNode", "test.json"
    )


def test_use_tmp_path(proj_path):
    with zntrack.Project(automatic_node_names=True) as proj:
        node = zntrack.examples.WriteDVCOuts(params="test")
        node2 = zntrack.examples.WriteDVCOutsPath(params="test2")

        node3 = zntrack.examples.WriteDVCOuts(params="test", outs="result.txt")
        node4 = zntrack.examples.WriteDVCOutsPath(
            params="test2", outs=(zntrack.nwd / "data").as_posix()
        )

    proj.build()
    proj.run()

    #     node = node.from_rev(node.name)
    #     node2 = node2.from_rev(node2.name)
    #     node3 = node3.from_rev(node3.name)
    #     node4 = node4.from_rev(node4.name)

    assert node.get_outs_content() == "test"
    assert node2.get_outs_content() == "test2"
    assert node3.get_outs_content() == "test"
    assert node4.get_outs_content() == "test2"

    assert node.outs == pathlib.Path("nodes", "WriteDVCOuts", "output.txt")
    assert node2.outs == pathlib.Path("nodes", "WriteDVCOutsPath", "data")
    assert node3.outs == "result.txt"
    assert isinstance(node4.outs, str)
    assert node4.outs == pathlib.Path("nodes", "WriteDVCOutsPath_1", "data").as_posix()

    #     # DOES THIS EVEN MAKE SENSE?
    #     # IDEA: do only use tmp_path if rev or remote is passed
    with node.state.use_tmp_path():
        assert node.outs == pathlib.Path("nodes", "WriteDVCOuts", "output.txt")
    with node2.state.use_tmp_path():
        assert node2.outs == pathlib.Path("nodes", "WriteDVCOutsPath", "data")
    with node3.state.use_tmp_path():
        assert node3.outs == "result.txt"
        assert isinstance(node3.outs, str)
    with node4.state.use_tmp_path():
        assert (
            node4.outs == pathlib.Path("nodes", "WriteDVCOutsPath_1", "data").as_posix()
        )

    #     # fake remote by passing the current directory
    node = node.from_rev(node.name)
    node2 = node2.from_rev(node2.name)
    node3 = node3.from_rev(node3.name)
    node4 = node4.from_rev(node4.name)

    assert node.get_outs_content() == "test"
    assert node2.get_outs_content() == "test2"
    assert node3.get_outs_content() == "test"
    assert node4.get_outs_content() == "test2"

    assert node.outs == pathlib.Path("nodes", "WriteDVCOuts", "output.txt")
    assert node2.outs == pathlib.Path("nodes", "WriteDVCOutsPath", "data")
    assert node3.outs == "result.txt"
    assert isinstance(node4.outs, str)
    assert node4.outs == pathlib.Path("nodes", "WriteDVCOutsPath_1", "data").as_posix()

    # load the nodes so we can use the tmp_path
    node = node.from_rev(node.name, remote=".")
    node2 = node2.from_rev(node2.name, remote=".")
    node3 = node3.from_rev(node3.name, remote=".")
    node4 = node4.from_rev(node4.name, remote=".")

    with node.state.use_tmp_path():
        assert node.state.tmp_path != pathlib.Path("nodes", "WriteDVCOuts")
        assert node.outs == node.state.tmp_path / "output.txt"
        assert isinstance(node.outs, pathlib.PurePath)
    with node2.state.use_tmp_path():
        assert node2.outs == node2.state.tmp_path / "data"
        assert isinstance(node2.outs, pathlib.PurePath)
    with node3.state.use_tmp_path():
        # no NWD, thus no tmp_path usage possible (as of yet)
        assert node3.outs == "result.txt"
        # assert node3.outs == (node3.state.tmp_path / "result.txt").as_posix()
        assert isinstance(node3.outs, str)
    with node4.state.use_tmp_path():
        assert node4.outs == (node4.state.tmp_path / "data").as_posix()
        assert isinstance(node4.outs, str)


def test_use_tmp_path_multi(proj_path):
    with zntrack.Project(automatic_node_names=True) as proj:
        node = zntrack.examples.WriteMultipleDVCOuts(params=["Lorem", "Ipsum", "Dolor"])

    proj.build()
    proj.run()

    assert node.get_outs_content() == ("Lorem", "Ipsum", "Dolor")

    assert node.outs1 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "output.txt")
    assert node.outs2 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "output2.txt")
    assert node.outs3 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "data")

    with node.state.use_tmp_path():
        assert node.state.tmp_path != pathlib.Path("nodes", "WriteMultipleDVCOuts")
        assert node.outs1 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "output.txt")
        assert node.outs2 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "output2.txt")
        assert node.outs3 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "data")

        assert pathlib.Path(node.outs1).read_text() == "Lorem"
        assert pathlib.Path(node.outs2).read_text() == "Ipsum"
        assert (pathlib.Path(node.outs3) / "file.txt").read_text() == "Dolor"

    node = node.from_rev(remote=".")  # fake remote by passing the current directory

    with node.state.use_tmp_path():
        assert node.state.tmp_path != pathlib.Path("nodes", "WriteMultipleDVCOuts")
        assert node.outs1 == (node.state.tmp_path / "output.txt")
        assert node.outs2 == (node.state.tmp_path / "output2.txt")
        assert node.outs3 == (node.state.tmp_path / "data")

        assert pathlib.Path(node.outs1).read_text() == "Lorem"
        assert pathlib.Path(node.outs2).read_text() == "Ipsum"
        assert (pathlib.Path(node.outs3) / "file.txt").read_text() == "Dolor"


def test_use_tmp_path_sequence(proj_path):
    with zntrack.Project(automatic_node_names=True) as proj:
        node = zntrack.examples.WriteDVCOutsSequence(
            params=["Lorem", "Ipsum", "Dolor"],
            outs=[zntrack.nwd / x for x in ["output.txt", "output2.txt", "output3.txt"]],
        )

    proj.build()
    proj.run()

    assert node.outs == [
        pathlib.Path("nodes", "WriteDVCOutsSequence", "output.txt"),
        pathlib.Path("nodes", "WriteDVCOutsSequence", "output2.txt"),
        pathlib.Path("nodes", "WriteDVCOutsSequence", "output3.txt"),
    ]

    for outs in node.outs:
        assert pathlib.Path(outs).exists()

    with node.state.use_tmp_path():
        for outs in node.outs:
            assert pathlib.Path(outs).exists()
            assert pathlib.Path(outs).read_text() in ("Lorem", "Ipsum", "Dolor")
            assert pathlib.Path(outs).parent == pathlib.Path(
                "nodes", "WriteDVCOutsSequence"
            )

    assert node.get_outs_content() == ["Lorem", "Ipsum", "Dolor"]

    node = node.from_rev(remote=".")  # fake remote by passing the current directory

    with node.state.use_tmp_path():
        for outs in node.outs:
            assert pathlib.Path(outs).exists()
            assert pathlib.Path(outs).read_text() in ("Lorem", "Ipsum", "Dolor")
            assert pathlib.Path(outs).parent == node.state.tmp_path

    assert node.get_outs_content() == ["Lorem", "Ipsum", "Dolor"]


# def test_use_tmp_path_exp(tmp_path_2):
#     with zntrack.Project(automatic_node_names=True) as proj:
#         node = zntrack.examples.WriteDVCOuts(params="test")

#     proj.build()
#     proj.run()

#     with proj.create_experiment() as exp1:
#         node.params = "test1"

#     with proj.create_experiment() as exp2:
#         node.params = "test2"

#     proj.run_exp()

#     exp1.load()
#     node1 = exp1["WriteDVCOuts"]
#     assert node1.get_outs_content() == "test1"

#     with node1.state.use_tmp_path():
#         assert node1.outs == node1.state.tmp_path / "output.txt"
#         assert isinstance(node1.outs, pathlib.PurePath)
#         assert pathlib.Path(node1.outs).read_text() == "test1"

#     exp2.load()
#     node2 = exp2["WriteDVCOuts"]
#     assert node2.get_outs_content() == "test2"

#     with node2.state.use_tmp_path():
#         assert node2.outs == node2.state.tmp_path / "output.txt"
#         assert isinstance(node2.outs, pathlib.PurePath)
#         assert pathlib.Path(node2.outs).read_text() == "test2"

#     assert node.get_outs_content() == "test"
#     assert node.outs == pathlib.Path("nodes", "WriteDVCOuts", "output.txt")

#     with node.state.use_tmp_path():
#         assert node.outs == pathlib.Path("nodes", "WriteDVCOuts", "output.txt")
#         assert pathlib.Path(node.outs).read_text() == "test"
