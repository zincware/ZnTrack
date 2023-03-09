""""""
from pathlib import Path

import zntrack


class StageIO(zntrack.Node):
    outs = zntrack.dvc.outs(Path("calculation.txt"))
    deps = zntrack.dvc.deps()
    param = zntrack.zn.params()

    def __init__(self, file=None, **kwargs):
        """Class constructor
        Definition of parameters and results
        """
        super().__init__(**kwargs)
        self.param = file
        self.deps = file

    def run(self):
        """Actual computation"""

        with open(self.deps, "r") as f:
            file_content = f.readlines()

        Path(self.outs).write_text("".join(file_content))


class StageAddition(zntrack.Node):
    outs = zntrack.dvc.outs(Path("calculation.txt"))

    n_1 = zntrack.zn.params()  # seems optional now
    n_2 = zntrack.zn.params()

    sum = zntrack.zn.outs()
    dif = zntrack.zn.outs()

    def __init__(self, n_1=None, n_2=None, **kwargs):
        """Class constructor
        Definition of parameters and results
        """
        super().__init__(**kwargs)
        self.n_1 = n_1
        self.n_2 = n_2

    def run(self):
        """Actual computation"""
        self.sum = self.n_1 + self.n_2
        self.dif = self.n_1 - self.n_2

        Path(self.outs).write_text(f"{self.n_1} + {self.n_2} = {self.sum}")


def test_stage_addition(tmp_path_2):
    """Check that the dvc repro works"""
    project = zntrack.Project()

    with project:
        node = StageAddition(5, 10)

    project.run()

    with project.create_experiment(name="exp1"):
        node

    with project.create_experiment(name="exp2"):
        node.n_1 = 50
        node.n_2 = 100

    project.run_exp()

    assert node.from_rev(rev="exp1").sum == 15
    assert node.from_rev(rev="exp2").sum == 150


# def test_stage_io(proj_path):
#     project = ZnTrackProject()
#     project.name = "Test1"

#     deps = Path("test_example_01.py").resolve()

#     stage_io = StageIO(file=deps)
#     assert stage_io.deps == deps
#     assert stage_io.param == deps
#     stage_io.write_graph()
#     # load
#     stage_io = StageIO.load()
#     assert stage_io.param == deps
#     assert stage_io.deps == deps
#     project.repro()

#     stage = StageIO.load()

#     assert stage.outs.read_text().startswith('"""')
