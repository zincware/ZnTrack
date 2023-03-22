import pytest

import zntrack


class GenerateList(zntrack.Node):
    size = zntrack.zn.params(10)
    outs = zntrack.zn.outs()

    def run(self):
        self.outs = list(range(self.size))


class AddOneToList(zntrack.Node):
    data = zntrack.zn.deps()
    outs = zntrack.zn.outs()

    def run(self) -> None:
        self.outs = [x + 1 for x in self.data]


class AddOneToDict(zntrack.Node):
    data = zntrack.zn.deps()
    outs = zntrack.zn.outs()

    def run(self) -> None:
        self.outs = {k: [x + 1 for x in v] for k, v in self.data.items()}


@pytest.mark.parametrize("eager", [True, False])
def test_combine(proj_path, eager):
    with zntrack.Project() as proj:
        a = GenerateList(size=1, name="a")
        b = GenerateList(size=2, name="b")
        c = GenerateList(size=3, name="c")

        added = AddOneToList(data=a.outs + b.outs + c.outs)

    proj.run(eager=eager)
    if not eager:
        added.load()

    assert added.outs == [1] + [1, 2] + [1, 2, 3]


@pytest.mark.parametrize("eager", [True, False])
def test_combine_dict(proj_path, eager):
    with zntrack.Project() as proj:
        a = GenerateList(size=1, name="a")
        b = GenerateList(size=2, name="b")
        c = GenerateList(size=3, name="c")

        added = AddOneToDict(data={"a": a.outs, "b": b.outs, "c": c.outs})

    proj.run(eager=eager)
    if not eager:
        added.load()

    assert added.outs == {"a": [1], "b": [1, 2], "c": [1, 2, 3]}
