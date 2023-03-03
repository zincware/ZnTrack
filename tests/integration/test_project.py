import time

import zntrack


class AddNumbers(zntrack.Node):
    a = zntrack.zn.params()
    b = zntrack.zn.params()
    result = zntrack.zn.outs()

    def run(self):
        self.result = self.a + self.b


class AddNodes(zntrack.Node):
    a = zntrack.zn.deps()
    b = zntrack.zn.deps()
    result = zntrack.zn.outs()

    def run(self):
        self.result = self.a.result + self.b.result


# TODO is there an eager mode to this?
def test_project(empty_path):
    with zntrack.Project() as project:
        a = AddNumbers(a=1, b=2)
        b = AddNumbers(a=3, b=4)
        c = AddNodes(a=a, b=b)
    project.run()

    project.load()  # Load is always inplace.
    project.get_nodes()["AddNodes"].result == 10


def test_experiments(empty_path):
    project = zntrack.Project()

    with project.create_branch("expA") as expa:
        node1 = AddNumbers(a=1, b=2)
    expa.queue("exp1")

    with project.create_branch("expB") as expb:
        node2 = AddNumbers(a=1, b=20)
    expb.queue("exp2")

    project.run_exp()
    assert node1.state.rev == "exp1"
    assert node2.state.rev == "exp2"
    node1.load()
    node2.load()
    assert node1.result == 3
    assert node2.result == 21


def test_experiments_reuse(empty_path):
    project = zntrack.Project()

    exp = project.create_branch("exp")
    with exp:
        _ = AddNumbers(a=1, b=2)
    exp.queue("exp1")

    with exp:
        _ = AddNumbers(a=1, b=20)
    exp.queue("exp2")

    project.run_exp()

    assert AddNumbers.from_rev(rev="exp1").result == 3
    assert AddNumbers.from_rev(rev="exp2").result == 21
