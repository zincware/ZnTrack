import os
import pathlib
import shutil
import subprocess
import typing

import pytest

from zntrack import dvc
from zntrack.core.base import Node


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class SingleNode(Node):
    path1: pathlib.Path = dvc.outs()

    def __init__(self, path_x=None, **kwargs):
        super().__init__(**kwargs)
        self.path1 = pathlib.Path(f"{path_x}.json")

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
    SingleNode(path_x="test", name="1500").write_graph(no_exec=False)

    assert SingleNode.load(name="1500").path1 == pathlib.Path("test.json")


def test_multiple_outs(proj_path):
    SingleNodeListOut(
        paths=[pathlib.Path("test_1.txt"), pathlib.Path("test_2.txt")]
    ).write_graph(no_exec=False)

    assert pathlib.Path("test_1.txt").read_text() == "Lorem Ipsum"
    assert pathlib.Path("test_2.txt").read_text() == "Lorem Ipsum"
    assert SingleNodeListOut.load().paths == [
        pathlib.Path("test_1.txt"),
        pathlib.Path("test_2.txt"),
    ]


class SingleNodeInNodeDir(Node):
    path1: pathlib.Path = dvc.outs(use_node_dir=True)

    def __init__(self, path_x=None, **kwargs):
        super().__init__(**kwargs)
        self.path1 = pathlib.Path(f"{path_x}.json")

    def run(self):
        self.path1.write_text("")


class SingleNodeInNodeDirDefault(Node):
    path1: pathlib.Path = dvc.outs(pathlib.Path("outs.txt"), use_node_dir=True)

    def run(self):
        self.path1.write_text("")


class ListNodeInNodeDirDefault(Node):
    path1: typing.List[pathlib.Path] = dvc.outs(
        [pathlib.Path("outs1.txt"), pathlib.Path("outs2.txt")], use_node_dir=True
    )

    def run(self):
        [x.touch() for x in self.path1]


def test_load_dvc_outs_node_dir(proj_path):
    node = SingleNodeInNodeDir(path_x="test", name="1500")
    assert node.path1 == pathlib.Path("nodes/1500/test.json")

    node.write_graph(run=True)

    assert SingleNodeInNodeDir["1500"].path1 == pathlib.Path("nodes/1500/test.json")


def test_load_dvc_outs_node_dir_default(proj_path):
    node = SingleNodeInNodeDirDefault()
    assert node.path1 == pathlib.Path("nodes/SingleNodeInNodeDirDefault/outs.txt")

    node.write_graph(run=True)

    assert SingleNodeInNodeDirDefault.load().path1 == pathlib.Path(
        "nodes/SingleNodeInNodeDirDefault/outs.txt"
    )


def test_ListNodeInNodeDirDefault():
    node = ListNodeInNodeDirDefault()
    assert node.path1 == [
        pathlib.Path("nodes/ListNodeInNodeDirDefault/outs1.txt"),
        pathlib.Path("nodes/ListNodeInNodeDirDefault/outs2.txt"),
    ]


def test_ListNodeInNodeDirDefaultSet():
    node = ListNodeInNodeDirDefault(
        path1=[pathlib.Path("outs1.txt"), pathlib.Path("outs2.txt")]
    )
    assert node.path1 == [
        pathlib.Path("nodes/ListNodeInNodeDirDefault/outs1.txt"),
        pathlib.Path("nodes/ListNodeInNodeDirDefault/outs2.txt"),
    ]


def test_modify_node_dir_outs():
    node = SingleNodeInNodeDir(path_x="test")
    with pytest.raises(ValueError):
        node.path1 = node.path1.with_suffix(".txt")
