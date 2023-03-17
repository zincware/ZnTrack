import pathlib

import pytest

import zntrack


class WriteToNWD(zntrack.Node):
    text = zntrack.zn.params()
    file: pathlib.Path = zntrack.dvc.outs([zntrack.nwd / "test.txt"])

    def run(self):
        self.nwd.mkdir(exist_ok=True, parents=True)
        self.file[0].write_text(self.text)
    
class OutsAsNWD(zntrack.Node):
    text = zntrack.zn.params()
    outs: pathlib.Path = zntrack.dvc.outs(zntrack.nwd)

    def run(self):
        (self.outs / "test.txt").write_text(self.text)


@pytest.mark.parametrize("eager", [True, False])
def test_WriteToNWD(proj_path, eager):
    with zntrack.Project() as project:
        write_to_nwd = WriteToNWD(text="Hello World")

    project.run(eager=eager)
    assert write_to_nwd.file[0].read_text() == "Hello World"
    assert write_to_nwd.file == [pathlib.Path("nodes", "WriteToNWD", "test.txt")]
    if not eager:
        write_to_nwd.load()
    assert write_to_nwd.__dict__["file"] == [pathlib.Path("$nwd$", "test.txt")]

@pytest.mark.parametrize("eager", [True, False])
def test_OutAsNWD(proj_path, eager):
    with zntrack.Project() as project:
        outs_as_nwd = OutsAsNWD(text="Hello World")

    project.run(eager=eager)
    assert (outs_as_nwd.outs / "test.txt").read_text() == "Hello World"
    assert outs_as_nwd.outs == pathlib.Path("nodes", "OutsAsNWD")
    if not eager:
        outs_as_nwd.load()
    assert outs_as_nwd.__dict__["outs"] == zntrack.nwd
