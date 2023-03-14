import pathlib
import subprocess

import pytest
import yaml

import zntrack


class NodeWithMeta(zntrack.Node):
    author = zntrack.meta.Text("Fabian")
    title = zntrack.meta.Text("Test Node")


class NodeWithEnv(zntrack.Node):
    OMP_NUM_THREADS = zntrack.meta.Environment("1")

    def run(self):
        import os

        assert os.environ["OMP_NUM_THREADS"] == self.OMP_NUM_THREADS


def test_NodeWithMeta(proj_path):
    NodeWithMeta().write_graph()

    node_w_meta = NodeWithMeta.from_rev()
    assert node_w_meta.author == "Fabian"

    dvc_yaml = yaml.safe_load(pathlib.Path("dvc.yaml").read_text())
    assert dvc_yaml["stages"]["NodeWithMeta"]["meta"] == {
        "author": "Fabian",
        "title": "Test Node",
    }


class CombinedNodeWithMeta(zntrack.Node):
    input: str = zntrack.zn.params("Hello ")
    output: str = zntrack.zn.outs()
    author: str = zntrack.meta.Text()

    def run(self):
        self.output = self.input + self.author


def test_CombinedNodeWithMeta(proj_path):
    with pytest.raises(TypeError):
        # should raise an error because author is missing as kwarg
        _ = CombinedNodeWithMeta()

    CombinedNodeWithMeta(author="World").write_graph(run=True)
    assert CombinedNodeWithMeta.from_rev().output == "Hello World"
    assert CombinedNodeWithMeta.from_rev().author == "World"

    CombinedNodeWithMeta(author="there").write_graph(run=True)
    # changing the 'meta.Text' should not trigger running the model again
    assert CombinedNodeWithMeta.from_rev().output == "Hello World"
    assert CombinedNodeWithMeta.from_rev().author == "there"

    zntrack.utils.run_dvc_cmd(["repro", "-f"])
    # Forcing rerun should use the updated meta keyword.
    assert CombinedNodeWithMeta.from_rev().output == "Hello there"


def test_NodeWithEnv(proj_path):
    with zntrack.Project() as proj:
        NodeWithEnv()  # the actual test is inside the run method.
    proj.run()
