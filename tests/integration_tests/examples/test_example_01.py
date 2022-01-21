""""""
import os
import shutil
from pathlib import Path

from zntrack import Node, ZnTrackProject, dvc, zn


class StageIO(Node):
    outs = dvc.outs(Path("calculation.txt"))
    deps = dvc.deps()
    param = zn.params()

    def __init__(self, file=None, *args, **kwargs):
        """Class constructor
        Definition of parameters and results
        """
        super().__init__(*args, **kwargs)
        self.param = file
        self.deps = file

    def run(self):
        """Actual computation"""

        with open(self.deps, "r") as f:
            file_content = f.readlines()

        Path(self.outs).write_text("".join(file_content))


class StageAddition(Node):
    outs = dvc.outs(Path("calculation.txt"))

    n_1 = zn.params()  # seems optional now
    n_2 = zn.params()

    sum = zn.outs()
    dif = zn.outs()

    def __init__(self, n_1=None, n_2=None, *args, **kwargs):
        """Class constructor
        Definition of parameters and results
        """
        super().__init__(*args, **kwargs)
        self.n_1 = n_1
        self.n_2 = n_2

    def run(self):
        """Actual computation"""
        self.sum = self.n_1 + self.n_2
        self.dif = self.n_1 - self.n_2

        Path(self.outs).write_text(f"{self.n_1} + {self.n_2} = {self.sum}")


def test_stage_addition(tmp_path):
    """Check that the dvc repro works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    StageAddition(5, 10).write_graph()
    project.name = "Test1"
    project.queue()

    StageAddition(50, 100).write_graph()
    project.name = "Test2"
    project.run()
    project.repro()

    project.load("Test1")
    finished_stage = StageAddition.load()
    assert finished_stage.sum == 15

    project.load("Test2")
    finished_stage = StageAddition.load()
    assert finished_stage.sum == 150


def test_stage_io(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "Test1"
    project.create_dvc_repository()

    deps = Path("test_example_01.py").resolve()

    stage_io = StageIO(file=deps)
    assert stage_io.deps == deps
    assert stage_io.param == deps
    stage_io.write_graph()
    # load
    stage_io = StageIO.load()
    assert stage_io.param == deps
    assert stage_io.deps == deps
    project.repro()

    stage = StageIO.load()

    assert stage.outs.read_text().startswith('"""')
