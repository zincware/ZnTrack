import dataclasses
import typing

from zntrack import Node, dvc, zn


@dataclasses.dataclass
class Params:
    param: int = 1


class CustomDeps(Node):
    outs = zn.outs()
    param: Params = zn.Method()

    def __init__(self, param=None, **kwargs):
        super().__init__(**kwargs)
        self.param = param

    def run(self):
        self.outs = self.param.param


class DepsCollector(Node):
    deps: typing.List[CustomDeps] = dvc.deps(
        [CustomDeps.load(name="Deps1"), CustomDeps.load(name="Deps2")]
    )
    outs = zn.outs()

    def run(self):
        self.outs = sum(x.outs for x in self.deps)


def test_multi_deps(proj_path):
    DepsCollector().write_graph()


# better error messages


class OutNotWritten(Node):
    outs = dvc.outs("does_not_exist.txt")

    def run(self):
        pass


def test_OutNotWritten(proj_path):
    OutNotWritten().write_graph(run=True)
