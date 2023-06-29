import pathlib

import pytest

import zntrack


class WriteToNWD(zntrack.Node):
    text = zntrack.zn.params()
    file: pathlib.Path = zntrack.dvc.outs([zntrack.nwd / "test.txt"])

    def run(self):
        self.nwd.mkdir(exist_ok=True, parents=True)
        self.file[0].write_text(self.text)


class FileToOuts(zntrack.Node):
    # although, this is a file path, it has to be zn.deps
    file = zntrack.zn.deps()
    text = zntrack.zn.outs()

    def run(self):
        with open(self.file[0], "r") as f:
            self.text = f.read()


@pytest.mark.parametrize("eager", [True, False])
def test_WriteToNWD(proj_path, eager):
    with zntrack.Project() as project:
        write_to_nwd = WriteToNWD(text="Hello World")
        file_to_outs = FileToOuts(file=write_to_nwd.file)

    project.run(eager=eager)
    assert write_to_nwd.file[0].read_text() == "Hello World"
    assert write_to_nwd.file == [pathlib.Path("nodes", "WriteToNWD", "test.txt")]
    if not eager:
        write_to_nwd.load()
    assert write_to_nwd.__dict__["file"] == [pathlib.Path("$nwd$", "test.txt")]

    file_to_outs.load()
    assert file_to_outs.text == "Hello World"


def test_OutAsNWD(proj_path):
    with pytest.raises(ValueError):

        class OutsAsNWD(zntrack.Node):
            text = zntrack.zn.params()
            outs: pathlib.Path = zntrack.dvc.outs(zntrack.nwd)
