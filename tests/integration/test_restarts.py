import subprocess

import zntrack.examples


def test_no_restart(tmp_path_2):
    project = zntrack.Project()

    with project:
        node = zntrack.examples.NodeWithRestart(start=0)

    assert node.state.run_count == 0

    project.run()

    # node.load()
    assert node.count == 1
    assert node.state.run_count == 1
    assert node.state.restarted is False


def test_restarts(tmp_path_2):
    project = zntrack.Project()

    with project:
        node = zntrack.examples.NodeWithRestart(start=0, raise_exception_until=2)

    project.build()
    # can not longer use project.run() because it will remove outputs, running manually
    # this should raise an exception
    results = subprocess.run(
        ["zntrack", "run", "zntrack.examples.NodeWithRestart", "--name=NodeWithRestart"]
    )
    assert results.returncode == 1
    # this should succeed
    results = subprocess.run(
        ["zntrack", "run", "zntrack.examples.NodeWithRestart", "--name=NodeWithRestart"]
    )
    assert results.returncode == 0

    node = node.from_rev(node.name)
    assert node.count == 2
    assert node.state.run_count == 2
    assert node.state.restarted is True
