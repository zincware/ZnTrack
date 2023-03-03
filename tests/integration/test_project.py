import pytest

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


def test_branches(empty_path):
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


def test_branch_reuse(empty_path):
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

def test_branches_reuse(empty_path):
    project = zntrack.Project()

    expa = project.create_branch("expA")
    with expa:
        _ = AddNumbers(a=1, b=2, name="A")
    expa.queue("exp1")
    with expa:
        _ = AddNumbers(a=1, b=3, name="A")
    expa.queue("exp2")

    expb = project.create_branch("expB")
    with expb:
        _ = AddNumbers(a=1, b=2, name="B")
    expb.queue("exp3")
    with expb:
        _ = AddNumbers(a=1, b=3, name="B")
    expb.queue("exp4")

    project.run_exp()

    assert AddNumbers.from_rev("A", rev="exp1").result == 3
    assert AddNumbers.from_rev("A", rev="exp2").result == 4

    assert AddNumbers.from_rev("B", rev="exp3").result == 3
    assert AddNumbers.from_rev("B", rev="exp4").result == 4

    with pytest.raises(KeyError):
        # TODO this should be a more specific error.
        _ = AddNumbers.from_rev("B", rev="exp1")
    
    with pytest.raises(KeyError):
        _ = AddNumbers.from_rev("A", rev="exp3")