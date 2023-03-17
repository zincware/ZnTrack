import pathlib

import pytest

import zntrack


class LoadFromDeps(zntrack.Node):
    data = zntrack.zn.deps()
    file: pathlib.Path = zntrack.dvc.deps()

    result = zntrack.zn.outs()

    def get_data(self):
        if self.data is not None:
            return self.data
        elif self.file is not None:
            return self.file.read_text()
        else:
            raise ValueError("No data provided")

    def run(self):
        self.result = self.get_data()


class WriteData(zntrack.Node):
    data = zntrack.zn.params()
    outs = zntrack.zn.outs()

    def run(self):
        self.outs = self.data


@pytest.mark.parametrize("value", ["data", "file"])
def test_init(value):
    with pytest.raises(TypeError):
        # setting only one of the deps args raise a requirement TypeError
        LoadFromDeps(**{value: None})


@pytest.mark.parametrize("eager", [True, False])
def test_from_zn_deps(proj_path, eager):
    with zntrack.Project(proj_path) as proj:
        data = WriteData(data="Hello World")
        node = LoadFromDeps(data=data.outs, file=None)
    proj.run(eager=eager)
    if not eager:
        node.load()

    assert node.result == "Hello World"


@pytest.mark.parametrize("eager", [True, False])
def test_from_dvc_deps(proj_path, eager):
    file = proj_path / "data.txt"
    file.write_text("Hello World")
    with zntrack.Project(proj_path) as proj:
        node = LoadFromDeps(file=file, data=None)

    proj.run(eager=eager)
    if not eager:
        node.load()

    assert node.result == "Hello World"
