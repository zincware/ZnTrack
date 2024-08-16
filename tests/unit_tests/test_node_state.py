import dataclasses

import dvc.api
import pytest

import zntrack
from zntrack.config import NodeStatusEnum

class MyNode(zntrack.Node):

    def run(self):
        pass


def test_state_get(proj_path):
    with zntrack.Project() as project:
        n = MyNode()

    project.build()
    assert n.state.remote == "."
    assert n.state.rev is None
    assert n.state.run_count == 0
    assert not n.state.restarted
    assert n.state.state == NodeStatusEnum.CREATED

    assert isinstance(n.state.fs, dvc.api.DVCFileSystem)


def test_state_get_after_run(proj_path):
    with zntrack.Project() as project:
        n = MyNode()

    project.build()
    assert n.state.state == NodeStatusEnum.CREATED
    project.run()

    assert n.state.remote == "."
    assert n.state.rev is None
    assert n.state.run_count == 1
    assert not n.state.restarted
    assert n.state.state == NodeStatusEnum.FINISHED

    # now test the loaded node
    n = n.from_rev()

    assert n.state.remote == "."
    assert n.state.rev is None
    assert n.state.run_count == 1
    assert not n.state.restarted
    assert n.state.state == NodeStatusEnum.FINISHED

def test_state_set(proj_path):
    with zntrack.Project() as project:
        n = MyNode()

    project.build()
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.remote = "remote"
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.rev = "rev"
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.run_count = 1
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.state = NodeStatusEnum.RUNNING
