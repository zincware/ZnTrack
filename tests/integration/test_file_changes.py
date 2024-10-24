import pathlib

import zntrack
from zntrack import Node, Project


class ChangeParamsInRun(Node):
    param: str = zntrack.params()

    def run(self):
        self.param = "incorrect param"


def test_ChangeParamsInRun(proj_path):
    with Project() as proj:
        ChangeParamsInRun(param="correct param")
    proj.repro()

    assert ChangeParamsInRun.from_rev().param == "correct param"


class ChangeJsonInRun(Node):
    outs: pathlib.Path = zntrack.outs_path(pathlib.Path("correct_out.txt"))

    def run(self):
        # need to create the file because DVC will fail otherwise
        self.outs.write_text("Create Correct File")
        self.outs = pathlib.Path("incorrect_out.txt")


def test_ChangeJsonInRun(proj_path):
    with Project() as proj:
        ChangeJsonInRun()
    proj.repro()
    assert ChangeJsonInRun.from_rev().outs == pathlib.Path("correct_out.txt")


class WriteToOutsOutsideRun(Node):
    outs: str = zntrack.outs()

    # def __init__(self, outs=None, **kwargs):
    #     super().__init__(**kwargs)
    #     self.outs = outs

    def run(self):
        self.outs = "correct outs"
