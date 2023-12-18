import pathlib
import typing

import zntrack.examples
from zntrack import Node, dvc, nwd


class SingleNode(Node):
    path1: pathlib.Path = dvc.outs()

    def __init__(self, path_x=None, **kwargs):
        super().__init__(**kwargs)
        self.path1 = pathlib.Path(f"{path_x}.json")

    def run(self):
        self.path1.write_text("")


class SingleNodeDefaultNWD(Node):
    path1: pathlib.Path = dvc.outs(nwd / "test.json")

    def run(self):
        self.path1.write_text("")


class SingleNodeListOut(Node):
    paths: typing.List[pathlib.Path] = dvc.outs()

    def __init__(self, paths=None, **kwargs):
        super().__init__(**kwargs)
        self.paths = paths

    def run(self):
        for path in self.paths:
            path.write_text("Lorem Ipsum")


def test_load_dvc_outs(proj_path):
    with zntrack.Project() as proj:
        node = SingleNode(path_x="test", name="1500")

    proj.build()

    node.load()
    assert node.path1 == pathlib.Path("test.json")

    assert SingleNode.from_rev(name="1500").path1 == pathlib.Path("test.json")


def test_multiple_outs(proj_path):
    with zntrack.Project() as proj:
        SingleNodeListOut(paths=[pathlib.Path("test_1.txt"), pathlib.Path("test_2.txt")])
    proj.run()

    assert pathlib.Path("test_1.txt").read_text() == "Lorem Ipsum"
    assert pathlib.Path("test_2.txt").read_text() == "Lorem Ipsum"
    assert SingleNodeListOut.from_rev().paths == [
        pathlib.Path("test_1.txt"),
        pathlib.Path("test_2.txt"),
    ]


class SingleNodeInNodeDir(Node):
    path: pathlib.Path = dvc.outs(nwd / "test.json")

    def run(self):
        self.nwd.mkdir(parents=True, exist_ok=True)
        if isinstance(self.path, list):
            [pathlib.Path(x).touch() for x in self.path]
        else:
            self.path.write_text("")


def test_SingleNodeInNodeDir(proj_path):
    with zntrack.Project() as proj:
        SingleNodeInNodeDir()
    proj.run()

    result = SingleNodeInNodeDir.from_rev()
    assert result.path == pathlib.Path("nodes", "SingleNodeInNodeDir", "test.json")
    assert result.path.exists()


def test_SingleNodeInNodeDirMulti(proj_path):
    with zntrack.Project() as proj:
        SingleNodeInNodeDir(path=[nwd / "test.json", "file.txt"], name="TestNode")
    proj.run()

    result = SingleNodeInNodeDir.from_rev(name="TestNode")
    assert result.path == [pathlib.Path("nodes", "TestNode", "test.json"), "file.txt"]
    assert all(pathlib.Path(x).exists() for x in result.path)


def test_SingleNodeDefaultNWD(proj_path):
    with zntrack.Project() as proj:
        SingleNodeDefaultNWD(name="SampleNode")
        SingleNodeDefaultNWD()
    proj.run()
    assert SingleNodeDefaultNWD.from_rev().path1 == pathlib.Path(
        "nodes", "SingleNodeDefaultNWD", "test.json"
    )
    assert SingleNodeDefaultNWD.from_rev(name="SampleNode").path1 == pathlib.Path(
        "nodes", "SampleNode", "test.json"
    )


def test_use_tmp_paths(proj_path):
    with zntrack.Project(automatic_node_names=True) as proj:
        node = zntrack.examples.WriteDVCOuts(params="test")
        node2 = zntrack.examples.WriteDVCOutsPath(params="test2")

        node3 = zntrack.examples.WriteDVCOuts(params="test", outs="result.txt")
        node4 = zntrack.examples.WriteDVCOutsPath(
            params="test2", outs=(zntrack.nwd / "data").as_posix()
        )

    proj.run()

    node.get_outs_content() == "test"
    node2.get_outs_content() == "test2"
    node3.get_outs_content() == "test"
    node4.get_outs_content() == "test2"

    assert node.outs == pathlib.Path("nodes", "WriteDVCOuts", "output.txt")
    assert node2.outs == pathlib.Path("nodes", "WriteDVCOutsPath", "data")
    assert node3.outs == "result.txt"
    assert isinstance(node4.outs, str)
    assert node4.outs == pathlib.Path("nodes", "WriteDVCOutsPath_1", "data").as_posix()

    with node.state.use_tmp_paths():
        assert node.outs == node.state.tmp_path / "output.txt"
        assert isinstance(node.outs, pathlib.PurePath)
    with node2.state.use_tmp_paths():
        assert node2.outs == node2.state.tmp_path / "data"
        assert isinstance(node2.outs, pathlib.PurePath)
    with node3.state.use_tmp_paths():
        assert node3.outs == (node3.state.tmp_path / "result.txt").as_posix()
        assert isinstance(node3.outs, str)
    with node4.state.use_tmp_paths():
        assert node4.outs == (node4.state.tmp_path / "data").as_posix()
        assert isinstance(node4.outs, str)


def test_use_tmp_paths_multi(proj_path):
    with zntrack.Project(automatic_node_names=True) as proj:
        node = zntrack.examples.WriteMultipleDVCOuts(params=["Lorem", "Ipsum", "Dolor"])

    proj.run()

    assert node.get_outs_content() == ("Lorem", "Ipsum", "Dolor")

    assert node.outs1 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "output.txt")
    assert node.outs2 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "output2.txt")
    assert node.outs3 == pathlib.Path("nodes", "WriteMultipleDVCOuts", "data")

    with node.state.use_tmp_paths():
        assert node.outs1 == (node.state.tmp_path / "output.txt")
        assert node.outs2 == (node.state.tmp_path / "output2.txt")
        assert node.outs3 == (node.state.tmp_path / "data")

        assert pathlib.Path(node.outs1).read_text() == "Lorem"
        assert pathlib.Path(node.outs2).read_text() == "Ipsum"
        assert (pathlib.Path(node.outs3) / "file.txt").read_text() == "Dolor"


def test_use_tmp_paths_sequence(proj_path):
    with zntrack.Project(automatic_node_names=True) as proj:
        node = zntrack.examples.WriteDVCOutsSequence(
            params=["Lorem", "Ipsum", "Dolor"],
            outs=[zntrack.nwd / x for x in ["output.txt", "output2.txt", "output3.txt"]],
        )

    proj.run()

    assert node.outs == [
        pathlib.Path("nodes", "WriteDVCOutsSequence", "output.txt"),
        pathlib.Path("nodes", "WriteDVCOutsSequence", "output2.txt"),
        pathlib.Path("nodes", "WriteDVCOutsSequence", "output3.txt"),
    ]

    for outs in node.outs:
        assert pathlib.Path(outs).exists()

    with node.state.use_tmp_paths():
        for outs in node.outs:
            assert pathlib.Path(outs).exists()
            assert pathlib.Path(outs).read_text() in ("Lorem", "Ipsum", "Dolor")
            assert pathlib.Path(outs).parent == node.state.tmp_path

    assert node.get_outs_content() == ["Lorem", "Ipsum", "Dolor"]


def test_use_tmp_paths_exp(tmp_path_2):
    with zntrack.Project(automatic_node_names=True) as proj:
        node = zntrack.examples.WriteDVCOuts(params="test")

    proj.run()

    with proj.create_experiment() as exp1:
        node.params = "test1"

    with proj.create_experiment() as exp2:
        node.params = "test2"

    proj.run_exp()

    exp1.load()
    node1 = exp1["WriteDVCOuts"]
    assert node1.get_outs_content() == "test1"

    with node1.state.use_tmp_paths():
        assert node1.outs == node1.state.tmp_path / "output.txt"
        assert isinstance(node1.outs, pathlib.PurePath)
        assert pathlib.Path(node1.outs).read_text() == "test1"

    exp2.load()
    node2 = exp2["WriteDVCOuts"]
    assert node2.get_outs_content() == "test2"

    with node2.state.use_tmp_paths():
        assert node2.outs == node2.state.tmp_path / "output.txt"
        assert isinstance(node2.outs, pathlib.PurePath)
        assert pathlib.Path(node2.outs).read_text() == "test2"

    assert node.get_outs_content() == "test"
    assert node.outs == pathlib.Path("nodes", "WriteDVCOuts", "output.txt")

    with node.state.use_tmp_paths():
        assert node.outs == node.state.tmp_path / "output.txt"
        assert isinstance(node.outs, pathlib.PurePath)
        assert pathlib.Path(node.outs).read_text() == "test"
