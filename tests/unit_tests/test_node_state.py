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
    assert n.state.name == "MyNode"

    assert isinstance(n.state.fs, dvc.api.DVCFileSystem)


def test_state_get_after_run(proj_path):
    with zntrack.Project() as project:
        n = MyNode()

    project.build()
    assert n.state.get_stage().addressing == "MyNode"
    assert n.state.state == NodeStatusEnum.CREATED
    project.run()

    assert n.state.get_stage().addressing == "MyNode"
    assert (
        n.state.get_stage_lock()["cmd"]
        == "zntrack run test_node_state.MyNode --name MyNode"
    )
    assert "deps" not in n.state.get_stage_lock()
    assert len(n.state.get_stage_lock()["outs"]) == 1
    assert n.state.get_stage_lock()["outs"][0]["hash"] == "md5"
    assert n.state.get_stage_lock()["outs"][0]["path"] == "nodes/MyNode/node-meta.json"
    assert n.state.get_stage_lock()["outs"][0]["size"] == 64
    assert "md5" in n.state.get_stage_lock()["outs"][0]
    assert n.state.remote == "."
    assert n.state.rev is None
    assert n.state.run_count == 1
    assert not n.state.restarted
    assert n.state.state == NodeStatusEnum.FINISHED
    assert n.state.lazy_evaluation is True

    # now test the loaded node
    n = n.from_rev()

    assert n.state.remote == "."
    assert n.state.rev is None
    assert n.state.run_count == 1
    assert not n.state.restarted
    assert n.state.state == NodeStatusEnum.FINISHED
    assert n.state.lazy_evaluation is True

    # again just for lazy_evaluation=False
    n = n.from_rev(lazy_evaluation=False)
    assert n.state.lazy_evaluation is False


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
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.restarted = True
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.lazy_evaluation = False