import pathlib

import pytest

import zntrack


class OutsTmp(zntrack.Node):
    file: pathlib.Path = zntrack.outs_path(zntrack.nwd / "file.txt")
    path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "path")

    def run(self):
        self.path.mkdir(parents=True, exist_ok=True)

        self.file.write_text("Hello, World!")
        (self.path / "data.txt").write_text("Lorem Ipsum")


def test_outs_tmp(proj_path):
    project = zntrack.Project()
    with project:
        node = OutsTmp()

    project.repro()
    assert node.nwd == pathlib.Path("nodes", OutsTmp.__name__)
    with pytest.warns(
        UserWarning,
        match="The temporary path is not used when neither remote or rev are set.",
    ):
        with node.state.use_tmp_path() as path:
            assert node.nwd == pathlib.Path("nodes", OutsTmp.__name__)

    # temp path is not used when neither remote or rev are set.
    node = node.from_rev(remote=".")

    assert node.nwd == pathlib.Path("nodes", OutsTmp.__name__)

    with node.state.use_tmp_path() as path:
        assert node.nwd != pathlib.Path("nodes", OutsTmp.__name__)
        assert node.nwd == path
        assert node.file == path / "file.txt"
        assert node.path == path / "path"

        assert node.file.read_text() == "Hello, World!"
        assert (node.path / "data.txt").read_text() == "Lorem Ipsum"
