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

    result = zntrack.zn.outs()

    def run(self):
        import os

        assert os.environ["OMP_NUM_THREADS"] == self.OMP_NUM_THREADS

        self.result = os.environ["OMP_NUM_THREADS"]


class NodeWithEnvNone(zntrack.Node):
    OMP_NUM_THREADS = zntrack.meta.Environment(None)

    result = zntrack.zn.outs()

    def run(self):
        import os

        assert "OMP_NUM_THREADS" not in os.environ


class NodeWithEnvParam(NodeWithEnv):
    OMP_NUM_THREADS = zntrack.meta.Environment("1", is_parameter=True)


@pytest.mark.parametrize("eager", [True, False])
def test_NodeWithMeta(proj_path, eager):
    with zntrack.Project() as project:
        node_w_meta = NodeWithMeta()

    project.run(eager=eager)
    if not eager:
        node_w_meta.load()
        dvc_yaml = yaml.safe_load(pathlib.Path("dvc.yaml").read_text())
        assert dvc_yaml["stages"]["NodeWithMeta"]["meta"] == {
            "author": "Fabian",
            "title": "Test Node",
        }

    assert node_w_meta.author == "Fabian"


def test_NodeWithEnvNone(proj_path):
    with zntrack.Project() as proj:
        _ = NodeWithEnvNone()  # the actual test is inside the run method.
    proj.run()


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


@pytest.mark.parametrize("cls", [NodeWithEnv, NodeWithEnvParam])
def test_NodeWithEnv(proj_path, cls):
    with zntrack.Project() as proj:
        node = cls()  # the actual test is inside the run method.
    proj.run()

    # check that the env variable is set correctly
    node.load()
    assert node.result == "1"

    with proj:
        node = cls(OMP_NUM_THREADS="2")  # the actual test is inside the run method.
    proj.run()

    node.load()
    if cls == NodeWithEnvParam:
        # Parameter will cause rerun and the result is changed
        assert node.result == "2"
    else:
        # env is not a parameter and will not cause rerun
        assert node.result == "1"
