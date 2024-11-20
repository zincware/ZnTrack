import pathlib
import typing as t

import pytest

import zntrack


class LoadFromDeps(zntrack.Node):
    data: t.Optional[t.Any] = zntrack.deps()
    file: t.Optional[pathlib.Path] = zntrack.deps_path()

    result: t.Any = zntrack.outs()

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
    data: t.Any = zntrack.params()
    outs: t.Any = zntrack.outs()

    def run(self):
        self.outs = self.data


@pytest.mark.parametrize("value", ["data", "file"])
def test_init(value):
    with pytest.raises(TypeError):
        # setting only one of the deps args raise a requirement TypeError
        LoadFromDeps(**{value: None})


@pytest.mark.parametrize("eager", [True, False])
def test_from_zn_deps(proj_path, eager):
    with zntrack.Project() as proj:
        data = WriteData(data="Hello World")
        node = LoadFromDeps(data=data.outs, file=None)

    if eager:
        proj.run()
    else:
        proj.repro()

    assert node.result == "Hello World"


@pytest.mark.parametrize("eager", [True, False])
def test_from_dvc_deps(proj_path, eager):
    file = proj_path / "data.txt"
    file.write_text("Hello World")
    with zntrack.Project() as proj:
        node = LoadFromDeps(file=file, data=None)

    if eager:
        proj.run()
    else:
        proj.repro()

    assert node.result == "Hello World"


class EmptyNodesNode(zntrack.Node):
    # we use dvc.outs to generate zntrack.json
    file: pathlib.Path = zntrack.outs_path(zntrack.nwd / "file.txt")
    value: t.Optional[int] = zntrack.deps(None)
    outs: int = zntrack.outs()

    def run(self):
        if self.value is None:
            self.outs = 42
        else:
            self.outs = self.value
        self.file.write_text("Hello World")


@pytest.mark.parametrize("eager", [True, False])
def test_EmptyNode(proj_path, eager):
    with zntrack.Project() as project:
        node = EmptyNodesNode()
    if eager:
        project.run()
    else:
        project.repro()
    assert node.outs == 42
