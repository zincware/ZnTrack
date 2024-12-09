"""Test that the dataclass post_init works properly."""

import os
import pathlib

import git

import zntrack


class NodeWithPostInit(zntrack.Node):
    def __post_init__(self):
        self.value = 42

    def run(self):
        pass


class SavePostInitNode(zntrack.Node):
    inp: int = zntrack.params()
    outs: int = zntrack.outs()

    def __post_init__(self):
        assert not pathlib.Path("inp.txt").exists()
        pathlib.Path("inp.txt").write_text(str(self.inp))

    def run(self):
        self.outs = self.inp


def test_create_node_with_post_init_plain(proj_path):
    node = NodeWithPostInit()
    assert node.value == 42


def test_create_node_with_post_init_project(proj_path):
    project = zntrack.Project()
    with project:
        node = NodeWithPostInit()
    assert node.value == 42


def test_create_node_with_post_init_from_rev(proj_path):
    node = NodeWithPostInit.from_rev()
    assert node.value == 42


def test_run_node_with_post_init(proj_path):
    project = zntrack.Project()
    with project:
        node = NodeWithPostInit()
    project.run()
    assert node.value == 42


def test_repro_node_with_post_init(proj_path):
    project = zntrack.Project()
    with project:
        node = NodeWithPostInit()
    project.repro()
    assert node.value == 42
    assert NodeWithPostInit.from_rev().value == 42


def test_save_post_init(proj_path):
    project = zntrack.Project()
    file = pathlib.Path("inp.txt")
    with project:
        node = SavePostInitNode(inp=42)
    # just init will save the input
    assert file.read_text() == "42"
    file.unlink()
    assert not file.exists()

    project.repro()
    # # make a commit with all files
    repo = git.Repo(proj_path)
    repo.git.add(".")
    repo.index.commit("commit")

    # after repro the file should be there
    assert file.read_text() == "42"
    file.unlink()
    assert not file.exists()

    # when loading the node from rev the file should be there
    node = SavePostInitNode.from_rev()
    assert node.inp == 42
    assert node.outs == 42
    assert file.read_text() == "42"
    file.unlink()
    assert not file.exists()

    cwd = pathlib.Path.cwd().resolve().as_posix()

    # now we load it in a different directory
    os.mkdir("new_dir")
    os.chdir("new_dir")

    node = SavePostInitNode.from_rev(remote=cwd)
    assert node.inp == 42
    assert node.outs == 42
    assert file.read_text() == "42"
