import git
import pytest

import zntrack.examples


@pytest.mark.xfail(reason="pending implementation")
@pytest.mark.parametrize("automatic_node_names", [True, False])
def test_multiple_experiments(proj_path, automatic_node_names):
    with zntrack.Project(automatic_node_names=automatic_node_names) as proj:
        node = zntrack.examples.ParamsToOuts(1)
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
            node.params = exp

    nodes = [zntrack.examples.ParamsToOuts.from_rev(rev=f"exp{exp}") for exp in range(5)]
    for idx, node in enumerate(nodes):
        assert node.outs == idx
        assert node._external_

    with proj:  # test with / without automatic node names
        node2 = zntrack.examples.AddNodeNumbers(nodes)

    proj.run()
    node2.load()

    assert node2.sum == 10
