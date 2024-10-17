import uuid

import dvc.scm
import pytest

import zntrack.examples

# from zntrack.utils import NodeStatusResults


# @pytest.mark.xfail(reason="pending implementation")
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
    # assert node.state.state ==


@pytest.mark.xfail(reason="pending implementation")
def test_connect_from_remote(proj_path):
    node_a = zntrack.from_rev(
        "HelloWorld",
        remote="https://github.com/PythonFZ/ZnTrackExamples.git",
        rev="890c714",
    )

    node_b = zntrack.from_rev(
        "HelloWorld",
        remote="https://github.com/PythonFZ/ZnTrackExamples.git",
        rev="369fe8f",
    )

    assert node_a.random_number == 123
    assert node_b.random_number == 126

    with zntrack.Project() as project:
        node = zntrack.examples.AddOne(number=node_a.random_number)

    project.run()
    # node.load()

    assert node.outs == node_a.random_number + 1

    with zntrack.Project() as project:
        node = zntrack.examples.AddOne(number=node_b.random_number)

    project.run()
    # We can not use node.load() here and build again,
    # because it will convert connections to e.g. type int
    # and then we can not connect to the node anymore.
    # node.load()

    assert zntrack.from_rev(node.name).outs == node_b.random_number + 1

    project.build()


@pytest.mark.xfail(reason="pending implementation")
def test_two_nodes_connect_external(proj_path):
    node_a = zntrack.from_rev(
        "HelloWorld",
        remote="https://github.com/PythonFZ/ZnTrackExamples.git",
        rev="890c714",
    )

    with zntrack.Project(automatic_node_names=True) as project:
        node1 = zntrack.examples.AddOne(number=node_a.random_number)
        node2 = zntrack.examples.AddOne(number=node_a.random_number)

    project.run()

    # node1.load()
    # node2.load()

    assert node1.outs == node_a.random_number + 1
    assert node2.outs == node_a.random_number + 1
