from zntrack import Node, ZnTrackProject, dvc, zn


class CreateNumbers(Node):
    number = zn.outs()

    def run(self):
        self.number = 42


class AddOne(Node):
    inp = zn.deps(CreateNumbers.load())
    number = zn.outs()

    def run(self):
        self.number = self.inp.number + 1


class SubtractOne(Node):
    inp = zn.deps(CreateNumbers.load())
    number = zn.outs()

    def run(self):
        self.number = self.inp.number - 1


class Summation(Node):
    """Stage that is actually tested, containing the multiple dependencies"""

    inp = zn.deps([AddOne.load(), SubtractOne.load()])
    number = zn.outs()

    def run(self):
        self.number = self.inp[0].number + self.inp[1].number


class SummationTuple(Node):
    """Stage that is actually tested, containing the multiple dependencies

    Additionally testing for tuple conversion here!
    """

    inp = zn.deps((AddOne.load(), SubtractOne.load()))
    number = zn.outs()

    def run(self):
        self.number = self.inp[0].number + self.inp[1].number


def test_repro(proj_path):
    """Test that a single DVC.deps() can take a list of dependencies"""
    project = ZnTrackProject()

    CreateNumbers().write_graph()
    AddOne().write_graph()
    SubtractOne().write_graph()
    Summation().write_graph()
    SummationTuple().write_graph()

    project.repro()

    assert Summation.load().number == 84
    assert SummationTuple.load().number == 84
