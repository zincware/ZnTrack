import pathlib

from zntrack import Node, dvc, zn


class ChangeParamsInRun(Node):
    param = zn.params()

    def run(self):
        self.param = "incorrect param"


def test_ChangeParamsInRun(proj_path):
    ChangeParamsInRun(param="correct param").write_graph(run=True)

    assert ChangeParamsInRun.from_rev().param == "correct param"


class ChangeJsonInRun(Node):
    outs = dvc.outs(pathlib.Path("correct_out.txt"))

    def run(self):
        # need to create the file because DVC will fail otherwise
        self.outs.write_text("Create Correct File")
        self.outs = pathlib.Path("incorrect_out.txt")


def test_ChangeJsonInRun(proj_path):
    ChangeJsonInRun().write_graph(run=True)
    assert ChangeJsonInRun.from_rev().outs == pathlib.Path("correct_out.txt")


class WriteToOutsOutsideRun(Node):
    outs = zn.outs()

    def __init__(self, outs=None, **kwargs):
        super().__init__(**kwargs)
        self.outs = outs

    def run(self):
        self.outs = "correct outs"


# def test_WriteToOutsOutsideRun(proj_path):
#     node = WriteToOutsOutsideRun(outs="correct outs")
#     node.run()
#     node.save()
#
#     assert WriteToOutsOutsideRun.from_rev().outs == "correct outs"
#     # WriteToOutsOutsideRun(outs="incorrect outs").save()
#     # assert WriteToOutsOutsideRun.from_rev().outs == "correct outs"
