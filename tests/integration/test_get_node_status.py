import subprocess

import zntrack.examples
from zntrack.utils.state import get_node_status


def test_get_node_status(proj_path):
    project = zntrack.Project()

    with project:
        a = zntrack.examples.ParamsToOuts(params=42)
        b = zntrack.examples.ParamsToOuts(params=43)
        c = zntrack.examples.AddNodeNumbers(numbers=[a, b])

    project.build()

    subprocess.check_call(["dvc", "repro", a.name])

    assert get_node_status(a.name, remote=None, rev=None) is False
    assert get_node_status(b.name, remote=None, rev=None) is True
    assert get_node_status(c.name, remote=None, rev=None) is True
    assert get_node_status("non_existing_node", remote=None, rev=None) is None

    subprocess.check_call(["dvc", "repro"])

    assert get_node_status(a.name, remote=None, rev=None) is False
    assert get_node_status(b.name, remote=None, rev=None) is False
    assert get_node_status(c.name, remote=None, rev=None) is False

    a.params = 44
    project.build()

    assert get_node_status(a.name, remote=None, rev=None) is True
    assert get_node_status(b.name, remote=None, rev=None) is False
    assert (
        get_node_status(c.name, remote=None, rev=None) is False
    )  # DVC the deps have not been updated, so this still assumes it is True

    subprocess.check_call(["dvc", "repro", a.name])
    assert get_node_status(a.name, remote=None, rev=None) is False
    assert get_node_status(b.name, remote=None, rev=None) is False
    assert (
        get_node_status(c.name, remote=None, rev=None) is True
    )  # Now the deps have been updated, so this is True again
