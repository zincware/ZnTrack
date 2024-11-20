import pytest

import zntrack.examples


@pytest.mark.xfail(reason="pending implementation")
@pytest.mark.needs_internet
def test_get_nodes_remote(proj_path):
    nodes = zntrack.get_nodes(
        remote="https://github.com/PythonFZ/ZnTrackExamples.git", rev="890c714"
    )

    assert nodes["HelloWorld"].random_number == 123


@pytest.mark.xfail(reason="pending implementation")
def test_get_nodes(proj_path):
    with zntrack.Project(automatic_node_names=True) as proj:
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)

    with proj.group("example1"):
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)

    with proj.group("nested", "GRP1"):
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)
    with proj.group("nested", "GRP2"):
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)

    proj.run()

    nodes = zntrack.get_nodes(remote=proj_path, rev=None)

    assert nodes["ParamsToOuts"].outs == 15
    assert nodes["ParamsToOuts_1"].outs == 15
    assert nodes["example1_ParamsToOuts"].outs == 15
    assert nodes["example1_ParamsToOuts_1"].outs == 15
    assert nodes["nested_GRP1_ParamsToOuts"].outs == 15
    assert nodes["nested_GRP1_ParamsToOuts_1"].outs == 15
    assert nodes["nested_GRP2_ParamsToOuts"].outs == 15
    assert nodes["nested_GRP2_ParamsToOuts_1"].outs == 15
