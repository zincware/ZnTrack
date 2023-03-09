import zntrack


class CreateNumbers(zntrack.Node):
    number = zntrack.zn.outs()

    def run(self):
        self.number = 42


class AddOne(zntrack.Node):
    inp = zntrack.zn.deps()
    number = zntrack.zn.outs()

    def run(self):
        self.number = self.inp.number + 1


class SubtractOne(zntrack.Node):
    inp = zntrack.zn.deps()
    number = zntrack.zn.outs()

    def run(self):
        self.number = self.inp.number - 1


class Summation(zntrack.Node):
    """Stage that is actually tested, containing the multiple dependencies"""

    inp = zntrack.zn.deps()
    number = zntrack.zn.outs()

    def run(self):
        self.number = self.inp[0].number + self.inp[1].number


class SummationTuple(zntrack.Node):
    """Stage that is actually tested, containing the multiple dependencies

    Additionally testing for tuple conversion here!
    """

    inp = zntrack.zn.deps()
    number = zntrack.zn.outs()

    def run(self):
        self.number = self.inp[0].number + self.inp[1].number


def test_repro(proj_path):
    """Test that a single DVC.deps() can take a list of dependencies"""
    project = zntrack.Project()

    create_number = CreateNumbers()
    create_number.write_graph()

    add_one = AddOne(inp=create_number)
    add_one.write_graph()
    subtract_one = SubtractOne(inp=create_number)
    subtract_one.write_graph()

    Summation(inp=[add_one, subtract_one]).write_graph()
    SummationTuple(inp=(add_one, subtract_one)).write_graph()

    project.run()

    assert Summation.from_rev().number == 84
    assert SummationTuple.from_rev().number == 84
