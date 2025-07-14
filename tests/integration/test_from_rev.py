import tempfile
import uuid

import dvc.scm
import git
import pytest
from dvc.fs import DVCFileSystem

import zntrack.examples

# from zntrack.utils import NodeStatusResults


@pytest.mark.needs_internet
def test_module_not_installed():
    with pytest.raises(ModuleNotFoundError):
        zntrack.from_rev(
            "ASEMD",
            remote="https://github.com/IPSProjects/IPS-Water",
            rev="ca0eef0ccfcbfb72a82136849a9ca35eac8b7629",
        )


@pytest.mark.needs_internet
def test_commit_not_found():
    with pytest.raises(dvc.scm.RevError):
        zntrack.from_rev(
            "ASEMD",
            remote="https://github.com/IPSProjects/IPS-Water",
            rev="this-does-not-exist",
        )


def test_import_from_remote(proj_path):
    node: zntrack.examples.ParamsToMetrics = zntrack.from_rev(
        "ParamsToMetrics",
        remote="https://github.com/PythonFZ/zntrack-examples",
        rev="8d0c992",
    )
    assert node.params == {"loss": 0.1, "accuracy": 0.9}
    assert node.metrics == {"loss": 0.1, "accuracy": 0.9}
    assert node.name == "ParamsToMetrics"
    assert node.state.rev == "8d0c992"
    assert node.state.remote == "https://github.com/PythonFZ/zntrack-examples"
    assert node.uuid == uuid.UUID("65b1c652-6508-4ee5-816c-c2f3cec22cc7")
    assert (
        node.state.get_stage_hash()
        == "70cbf7993d07a6cd0266a0fc0a874e163bc6f464ecc82bb1367b18d24091853c"
    )
    assert (
        node.state.get_stage_hash(include_outs=True)
        == "0e2ec8fab1123c1259ccf96a9590c4b161fc44cf4d93f755699a8fe99c3afe4c"
    )


def test_import_from_remote_local(proj_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        git.Repo.clone_from(
            "https://github.com/PythonFZ/zntrack-examples", tmpdir, branch="main"
        )
        node: zntrack.examples.ParamsToMetrics = zntrack.from_rev(
            "ParamsToMetrics", remote=tmpdir, rev="8d0c992"
        )
        assert node.params == {"loss": 0.1, "accuracy": 0.9}
        assert node.metrics == {"loss": 0.1, "accuracy": 0.9}
        assert node.name == "ParamsToMetrics"
        assert node.state.rev == "8d0c992"
        assert node.state.remote == tmpdir
        assert node.uuid == uuid.UUID("65b1c652-6508-4ee5-816c-c2f3cec22cc7")
        assert (
            node.state.get_stage_hash()
            == "70cbf7993d07a6cd0266a0fc0a874e163bc6f464ecc82bb1367b18d24091853c"
        )
        assert (
            node.state.get_stage_hash(include_outs=True)
            == "0e2ec8fab1123c1259ccf96a9590c4b161fc44cf4d93f755699a8fe99c3afe4c"
        )


def test_connect_from_remote(proj_path):
    project = zntrack.Project()

    external_node: zntrack.examples.ParamsToMetrics = zntrack.from_rev(
        name="ParamsToMetrics",
        remote="https://github.com/PythonFZ/zntrack-examples",
        rev="59dac86",
    )

    with project:
        n1 = zntrack.examples.DepsToMetrics(
            deps=external_node.metrics,
        )
        n2 = zntrack.examples.DepsToMetrics(
            deps=external_node.metrics,
        )

    project.repro()

    assert external_node.metrics == {"accuracy": 0.9, "loss": 0.1}
    assert n1.metrics == {"accuracy": 0.9, "loss": 0.1}
    assert n2.metrics == {"accuracy": 0.9, "loss": 0.1}

    # TODO: test with different rev and assert that things changed!

    # raise NotImplementedError("This test is not done yet!")

    # node_a = zntrack.from_rev(
    #     "HelloWorld",
    #     remote="https://github.com/PythonFZ/ZnTrackExamples.git",
    #     rev="890c714",
    # )

    # node_b = zntrack.from_rev(
    #     "HelloWorld",
    #     remote="https://github.com/PythonFZ/ZnTrackExamples.git",
    #     rev="369fe8f",
    # )

    # assert node_a.random_number == 123
    # assert node_b.random_number == 126

    # with zntrack.Project() as project:
    #     node = zntrack.examples.AddOne(number=node_a.random_number)

    # project.repro()

    # assert node.outs == node_a.random_number + 1

    # with zntrack.Project() as project:
    #     node = zntrack.examples.AddOne(number=node_b.random_number)

    # project.run()
    # # We can not use node.load() here and build again,
    # # because it will convert connections to e.g. type int
    # # and then we can not connect to the node anymore.
    # # node.load()

    # assert zntrack.from_rev(node.name).outs == node_b.random_number + 1

    # project.build()


def test_connect_from_remote_local(proj_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        git.Repo.clone_from(
            "https://github.com/PythonFZ/zntrack-examples", tmpdir, branch="main"
        )
        project = zntrack.Project()

        external_node: zntrack.examples.ParamsToMetrics = zntrack.from_rev(
            "ParamsToMetrics",
            remote=tmpdir,
            rev="59dac86",
        )

        with project:
            n1 = zntrack.examples.DepsToMetrics(
                deps=external_node.metrics,
            )
            n2 = zntrack.examples.DepsToMetrics(
                deps=external_node.metrics,
            )

        project.repro()

        assert external_node.metrics == {"accuracy": 0.9, "loss": 0.1}
        assert external_node.params == {"accuracy": 0.9, "loss": 0.1}
        assert n1.metrics == {"accuracy": 0.9, "loss": 0.1}
        assert n2.metrics == {"accuracy": 0.9, "loss": 0.1}


def test_two_nodes_connect_external(proj_path):
    node_a: zntrack.examples.ParamsToOuts = zntrack.from_rev(
        name="NumericOuts",
        remote="https://github.com/PythonFZ/zntrack-examples",
        rev="de82dc7104ac3",
    )
    assert node_a.name == "NumericOuts"
    assert node_a.__dict__["nwd"].as_posix() == "nodes/NumericOuts"

    with zntrack.Project() as project:
        assert node_a.name == "NumericOuts"
        node1 = zntrack.examples.AddOne(number=node_a.outs)
        node2 = zntrack.examples.AddOne(number=node_a.outs)

    project.repro()

    assert node1.outs == node_a.outs + 1
    assert node2.outs == node_a.outs + 1


def test_remote_and_fs(proj_path):
    fs = DVCFileSystem(
        url="https://github.com/PythonFZ/zntrack-examples", rev="de82dc7104ac3"
    )
    with pytest.raises(ValueError):
        zntrack.from_rev(
            name="NumericOuts",
            remote="https://github.com/PythonFZ/zntrack-examples",
            fs=fs,
        )
    with pytest.raises(ValueError):
        zntrack.from_rev(name="NumericOuts", rev="de82dc7104ac3", fs=fs)

    node: zntrack.Node = zntrack.from_rev(name="NumericOuts", fs=fs)
    assert node.state.remote == "https://github.com/PythonFZ/zntrack-examples"
    assert node.state.rev.startswith("de82dc7104ac3")


def test_two_nodes_connect_external_local(proj_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        git.Repo.clone_from(
            "https://github.com/PythonFZ/zntrack-examples", tmpdir, branch="main"
        )
        node_a: zntrack.examples.ParamsToOuts = zntrack.from_rev(
            name="NumericOuts",
            remote=tmpdir,
            rev="de82dc7104ac3",
        )
        assert node_a.name == "NumericOuts"
        assert node_a.__dict__["nwd"].as_posix() == "nodes/NumericOuts"

        with zntrack.Project() as project:
            assert node_a.name == "NumericOuts"
            node1 = zntrack.examples.AddOne(number=node_a.outs)
            node2 = zntrack.examples.AddOne(number=node_a.outs)

        project.repro()

        assert node1.outs == node_a.outs + 1
        assert node2.outs == node_a.outs + 1
