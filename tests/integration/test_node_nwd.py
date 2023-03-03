import pathlib

import pytest

import zntrack


class WriteToNWD(zntrack.Node):
    text = zntrack.zn.params()
    file: pathlib.Path = zntrack.dvc.outs([zntrack.nwd / "test.txt"])

    def run(self):
        self.nwd.mkdir(exist_ok=True, parents=True)
        self.file[0].write_text(self.text)


@pytest.mark.parametrize("eager", [True, False])
def test_WriteToNWD(proj_path, eager):
    with zntrack.Project(eager=eager) as project:
        write_to_nwd = WriteToNWD(text="Hello World")

    project.run()
    assert write_to_nwd.file[0].read_text() == "Hello World"
    assert write_to_nwd.file == [pathlib.Path("nodes", "WriteToNWD", "test.txt")]
    write_to_nwd.load()
    assert write_to_nwd.__dict__["file"] == [pathlib.Path("$nwd$", "test.txt")]
