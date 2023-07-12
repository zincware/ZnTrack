import git
import pytest

import zntrack


class SaveNumber(zntrack.Node):
    inputs = zntrack.zn.params()
    outputs = zntrack.zn.outs()

    def run(self):
        self.outputs = self.inputs


class AddNumbers(zntrack.Node):
    numbers: list = zntrack.zn.deps()
    sum: int = zntrack.zn.outs()

    def run(self):
        self.sum = sum(x.outputs for x in self.numbers)


@pytest.mark.parametrize("automatic_node_names", [True, False])
def test_multiple_experiments(proj_path, automatic_node_names):
    with zntrack.Project(automatic_node_names=automatic_node_names) as proj:
        node = SaveNumber(1)
    proj.build()
    proj.repro()

    # node.load()
    # assert node.outputs == 1

    repo = git.Repo()
    # add and commit all files
    repo.git.add(A=True)
    repo.index.commit("commit1")

    for exp in range(5):
        with proj.create_experiment(f"exp{exp}", queue=False):
            node.inputs = exp

    nodes = [SaveNumber.from_rev(rev=f"exp{exp}") for exp in range(5)]
    for idx, node in enumerate(nodes):
        assert node.outputs == idx
        assert node._external_

    with proj:  # test with / without automatic node names
        node2 = AddNumbers(nodes)

    proj.run()
    node2.load()

    assert node2.sum == 10
