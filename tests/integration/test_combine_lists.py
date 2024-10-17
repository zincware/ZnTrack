import subprocess

import pytest
import znflow

import zntrack


class GenerateList(zntrack.Node):
    size: int = zntrack.params(10)
    outs: list = zntrack.outs()

    def run(self):
        self.outs = list(range(self.size))


class AddOneToList(zntrack.Node):
    data: list = zntrack.deps()
    outs: list = zntrack.outs()

    def run(self) -> None:
        assert isinstance(self.data, list)
        self.outs = [x + 1 for x in self.data]


class AddOneToDict(zntrack.Node):
    data: dict = zntrack.deps()
    outs: dict = zntrack.outs()

    def run(self) -> None:
        assert isinstance(self.data, dict)
        assert all(isinstance(v, list) for v in self.data.values())
        self.outs = {k: [x + 1 for x in v] for k, v in self.data.items()}


# TODO: combinedconnections need tests in files
@pytest.mark.parametrize("eager", [True, False])
def test_combined_connection(proj_path, eager):
    with zntrack.Project() as proj:
        a = GenerateList(size=1, name="a")
        b = GenerateList(size=2, name="b")
        c = GenerateList(size=3, name="c")

        data = a.outs + b.outs + c.outs
        added = AddOneToList(data=data)

    assert isinstance(data, znflow.CombinedConnections)
    proj.build()
    if eager:
        proj.run()
    else:
        subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)

    assert added.outs == [1] + [1, 2] + [1, 2, 3]


@pytest.mark.parametrize("eager", [True, False])
def test_combine_dict(proj_path, eager):
    with zntrack.Project() as proj:
        a = GenerateList(size=1, name="a")
        b = GenerateList(size=2, name="b")
        c = GenerateList(size=3, name="c")

        added = AddOneToDict(data={x.name: x.outs for x in [a, b, c]})

    proj.build()
    if eager:
        proj.run()
    else:
        subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)

    assert added.outs == {"a": [1], "b": [1, 2], "c": [1, 2, 3]}
