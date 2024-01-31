""" "ZnTrack provides two post methods: _post_load_ and _post_init_.

_post_load_ is called after the node is loaded from disk.
_post_init_ is called after the node is initialized (loaded values are not available).
_post_init_ is NOT called after Node.from_rev().
"""

import pathlib

import pytest

import zntrack


class PostLoad(zntrack.Node):
    """A node that uses the _post_load_ method."""

    file: pathlib.Path = zntrack.dvc.outs(zntrack.nwd / "file.txt")

    file_content: str

    def _post_load_(self):
        # _post_load_ is also called, when to Node is first run.
        if self.file.exists():
            self.file_content = self.file.read_text()

    def run(self):
        self.file.write_text("Hello World")


class PostInit(zntrack.Node):
    """A node that uses the _post_init_ method."""

    file = zntrack.dvc.outs()

    file_content: str

    def _post_init_(self):
        if len(pathlib.Path(self.file).parents) == 1:
            # move single output files to the nwd
            # Hint: Don't do this! This is just for testing.
            self.file = self.nwd / self.file

    def run(self):
        self.file.write_text("Hello World")


class PostLoadInitNode(zntrack.Node):
    file = zntrack.dvc.outs()

    file_content: str

    def _post_load_(self):
        # _post_load_ is also called, when to Node is first run.
        if self.file.exists():
            self.file_content = self.file.read_text()

    def _post_init_(self):
        if len(pathlib.Path(self.file).parents) == 1:
            # move single output files to the nwd
            # Hint: Don't do this! This is just for testing.
            self.file = self.nwd / self.file

    def run(self):
        self.file.write_text("Hello World")


@pytest.mark.parametrize("eager", [True, False])
def test_PostLoad(proj_path, eager):
    with zntrack.Project() as project:
        node = PostLoad()
    project.run(eager=eager)
    if eager:
        node.save()
    node.load()
    assert node.file_content == "Hello World"


@pytest.mark.parametrize("eager", [True, False])
def test_PostInit(proj_path, eager):
    with zntrack.Project() as project:
        node = PostInit(file="file.txt")
    project.run(eager=eager)
    if eager:
        node.save()
    node.load()
    assert node.file == node.nwd / "file.txt"


@pytest.mark.parametrize("eager", [True, False])
def test_PostLoadInitNode(proj_path, eager):
    with zntrack.Project() as project:
        node = PostLoadInitNode(file="file.txt")
    project.run(eager=eager)
    if eager:
        node.save()
    node.load()
    assert node.file == node.nwd / "file.txt"
    assert node.file_content == "Hello World"
