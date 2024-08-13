import zntrack
import pytest
import dataclasses
import dvc.api

class MyNode(zntrack.Node):
    
    def run(self):
        pass


def test_state_get(proj_path):
    with zntrack.Project() as project:
        n = MyNode()
    
    project.build()
    assert n.state.remote == "."
    assert n.state.rev is None
    assert n.state.run_counter == 0
    assert not n.state.restarted

    assert isinstance(n.state.fs, dvc.api.DVCFileSystem)

def test_state_set(proj_path):
    with zntrack.Project() as project:
        n = MyNode()
    
    project.build()
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.remote = "remote"
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.rev = "rev"
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.state.run_counter = 1