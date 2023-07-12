import uuid

import dvc.scm
import pytest

import zntrack
from zntrack.utils import NodeStatusResults


class AddOne(zntrack.Node):
    number: int = zntrack.zn.deps()
    outs: int = zntrack.zn.outs()

    def run(self) -> None:
        self.outs = self.number + 1


def test_module_not_installed():
    with pytest.raises(ModuleNotFoundError):
        zntrack.from_rev(
            "ASEMD",
            remote="https://github.com/IPSProjects/IPS-Water",
            rev="ca0eef0ccfcbfb72a82136849a9ca35eac8b7629",
        )


def test_commit_not_found():
    with pytest.raises(dvc.scm.RevError):
        zntrack.from_rev(
            "ASEMD",
            remote="https://github.com/IPSProjects/IPS-Water",
            rev="this-does-not-exist",
        )


def test_import_from_remote(proj_path):
    node = zntrack.from_rev(
        "HelloWorld",
        remote="https://github.com/PythonFZ/ZnTrackExamples.git",
        rev="fbb6ada",
    )
    assert node.max_number == 512
    assert node.random_number == 123
    assert node.name == "HelloWorld"
    assert node.state.rev == "fbb6ada"
    assert node.state.remote == "https://github.com/PythonFZ/ZnTrackExamples.git"
    assert node.state.results == NodeStatusResults.AVAILABLE
    assert node.uuid == uuid.UUID("1d2d5eef-c42b-4ff4-aa1f-837638fdf090")


def test_connect_from_remote(proj_path):
    node = zntrack.from_rev(
        "HelloWorld",
        remote="https://github.com/PythonFZ/ZnTrackExamples.git",
        rev="fbb6ada",
    )

    node._external_ = True

    with zntrack.Project() as project:
        node2 = AddOne(number=node.random_number)

    project.run()
    node2.load()

    assert node2.outs == 124
