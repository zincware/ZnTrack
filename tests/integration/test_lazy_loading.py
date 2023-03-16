import dataclasses

import pytest

import zntrack
from zntrack.utils import LazyOption


class WriteOutput(zntrack.Node):
    value = zntrack.zn.params()
    output = zntrack.zn.outs()

    def run(self) -> None:
        self.output = self.value


class CollectOutputs(zntrack.Node):
    nodes = zntrack.zn.deps()
    output = zntrack.zn.outs()

    def run(self) -> None:
        self.output = sum(x.output for x in self.nodes)


@pytest.mark.parametrize("eager", [True, False])
@pytest.mark.parametrize("lazy", [True, False])
def test_WriteOutput(proj_path, lazy, eager):
    with zntrack.config.updated_config(lazy=lazy):
        with zntrack.Project() as project:
            node = WriteOutput(value=42)
        project.run(eager=eager)

        if not eager:
            node.load()
        if lazy and not eager:
            assert node.__dict__["output"] is LazyOption
        else:
            assert node.__dict__["output"] is 42
        assert node.output == 42


@pytest.mark.parametrize("eager", [True, False])
@pytest.mark.parametrize("lazy", [True, False])
def test_CollectOutputs(proj_path, lazy, eager):
    with zntrack.config.updated_config(lazy=lazy):
        with zntrack.Project() as project:
            a = WriteOutput(value=17, name="a")
            b = WriteOutput(value=42, name="b")
            node = CollectOutputs(nodes=[a, b])
        project.run(eager=eager)

        if not eager:
            node.load()
        if lazy and not eager:
            assert node.__dict__["output"] is LazyOption
            assert node.__dict__["nodes"] is LazyOption
            assert node.nodes[0].__dict__["output"] is LazyOption
            assert node.nodes[1].__dict__["output"] is LazyOption
        else:
            assert node.__dict__["output"] is 59
            assert node.__dict__["nodes"][0].name == "a"
            assert node.__dict__["nodes"][1].name == "b"

        assert node.nodes[0].output == 17
        assert node.nodes[1].output == 42
        assert node.output == 59

        if not eager:
            # Check that non-lazy loading works
            node = node.from_rev(lazy=False)
            assert node.__dict__["output"] is 59
            assert node.__dict__["nodes"][0].name == "a"
            assert node.__dict__["nodes"][1].name == "b"
