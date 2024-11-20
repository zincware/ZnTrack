""""""

from pathlib import Path

import pytest

import zntrack


class StageIO(zntrack.Node):
    deps: Path = zntrack.deps_path()
    param: int = zntrack.params(1)
    outs: Path = zntrack.outs_path(Path("calculation.txt"))

    def run(self):
        """Actual computation"""
        with open(self.deps, "r") as f:
            file_content = f.readlines()

        Path(self.outs).write_text("".join(file_content))


class StageAddition(zntrack.Node):
    n_1: int = zntrack.params()
    n_2: int = zntrack.params()

    sum: int = zntrack.outs()
    dif: int = zntrack.outs()

    outs: Path = zntrack.outs_path(Path("calculation.txt"))

    def run(self):
        """Actual computation"""
        self.sum = self.n_1 + self.n_2
        self.dif = self.n_1 - self.n_2

        Path(self.outs).write_text(f"{self.n_1} + {self.n_2} = {self.sum}")


@pytest.mark.xfail(reason="Experiments not yet supported", strict=True)
def test_stage_addition(tmp_path_2):
    """Check that the dvc repro works"""
    project = zntrack.Project()

    with project:
        node = StageAddition(5, 10)

    project.repro()

    with project.create_experiment(name="exp1"):
        node

    with project.create_experiment(name="exp2"):
        node.n_1 = 50
        node.n_2 = 100

    project.run_exp()

    assert node.from_rev(rev="exp1").sum == 15
    assert node.from_rev(rev="exp2").sum == 150


def test_stage_io(proj_path):
    deps = Path("test_example_01.py").resolve()
    assert deps.is_file()

    with zntrack.Project() as project:
        stage_io = StageIO(deps=deps, param=1, name="Node")

    assert stage_io.deps == deps
    assert stage_io.param == 1
    assert stage_io.name == "Node"
    project.build()

    assert stage_io.param == 1
    assert stage_io.deps == deps
    project.run()

    assert stage_io.outs.read_text().startswith('"""')
