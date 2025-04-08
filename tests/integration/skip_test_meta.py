import typing as t

import pytest

import zntrack


class NodeWithMeta(zntrack.Node):
    author = zntrack.meta.Text("Fabian")
    title = zntrack.meta.Text("Test Node")


class NodeWithEnv(zntrack.Node):
    OMP_NUM_THREADS = zntrack.meta.Environment("1")

    result: t.Any = zntrack.outs()

    def run(self):
        import os

        assert os.environ["OMP_NUM_THREADS"] == self.OMP_NUM_THREADS, (
            f"{os.environ['OMP_NUM_THREADS']} != {self.OMP_NUM_THREADS}"
        )

        self.result = os.environ["OMP_NUM_THREADS"]


class NodeWithEnvNone(zntrack.Node):
    OMP_NUM_THREADS = zntrack.meta.Environment(None)

    result = zntrack.outs()

    def run(self):
        import os

        assert "OMP_NUM_THREADS" not in os.environ


class AssertGlobalEnv(zntrack.Node):
    def run(self):
        import os

        assert os.environ["ZNTRACK_EXAMPLE"] == "1"


class NodeWithEnvParam(NodeWithEnv):
    OMP_NUM_THREADS = zntrack.meta.Environment("1", is_parameter=True)


def test_GlobalEnv(proj_path):
    with zntrack.Project() as proj:
        _ = AssertGlobalEnv()
    proj.run(environment={"ZNTRACK_EXAMPLE": "1"})


@pytest.mark.parametrize("eager", [True, False])
def test_NodeWithMeta(proj_path, eager):
    with zntrack.Project() as project:
        node_w_meta = NodeWithMeta()

    project.run(eager=eager)
    # if not eager:
    #     node_w_meta.load()

    assert node_w_meta.author == "Fabian"


def test_NodeWithEnvNone(proj_path):
    with zntrack.Project() as proj:
        _ = NodeWithEnvNone()  # the actual test is inside the run method.
    proj.run()


class CombinedNodeWithMeta(zntrack.Node):
    input: str = zntrack.params("Hello ")
    output: str = zntrack.outs()
    author: str = zntrack.meta.Text()

    def run(self):
        self.output = self.input + self.author


def test_CombinedNodeWithMeta(proj_path):
    with pytest.raises(TypeError):
        # should raise an error because author is missing as kwarg
        _ = CombinedNodeWithMeta()

    with zntrack.Project() as proj:
        node = CombinedNodeWithMeta(author="World")
    proj.run()
    assert CombinedNodeWithMeta.from_rev().output == "Hello World"
    assert CombinedNodeWithMeta.from_rev().author == "World"

    node.author = "there"
    proj.run()

    # changing the 'meta.Text' should not trigger running the model again
    assert CombinedNodeWithMeta.from_rev().output == "Hello World"
    assert CombinedNodeWithMeta.from_rev().author == "there"

    zntrack.utils.run_dvc_cmd(["repro", "-f"])
    # Forcing rerun should use the updated meta keyword.
    assert CombinedNodeWithMeta.from_rev().output == "Hello there"


@pytest.mark.parametrize("cls", [NodeWithEnv, NodeWithEnvParam])
def test_NodeWithEnv(proj_path, cls):
    with zntrack.Project(force=True, automatic_node_names=False) as proj:
        node = cls()  # the actual test is inside the run method.
    proj.run()

    # check that the env variable is set correctly
    # node.load()
    assert node.result == "1"

    with proj:
        node = cls(OMP_NUM_THREADS="2")  # the actual test is inside the run method.
    proj.run()

    # node.load()
    if cls == NodeWithEnvParam:
        # Parameter will cause rerun and the result is changed
        assert node.result == "2"
    else:
        # env is not a parameter and will not cause rerun
        assert node.result == "1"


class EnvAsDict(zntrack.Node):
    env: dict = zntrack.meta.Environment({"OMP_NUM_THREADS": "1"})
    SPECIAL_ENV = zntrack.meta.Environment()

    def run(self):
        import os

        assert self.env["OMP_NUM_THREADS"] == "1"
        assert os.environ["OMP_NUM_THREADS"] == self.env["OMP_NUM_THREADS"]
        assert os.environ["ZNTRACK_EXAMPLE"] == "1"
        assert os.environ["SPECIAL_ENV"] == "25"


def test_EnvAsDict(proj_path):
    with zntrack.Project() as proj:
        _ = EnvAsDict(SPECIAL_ENV="25")  # the actual test is inside the run method.
    proj.run(environment={"ZNTRACK_EXAMPLE": "1"})
