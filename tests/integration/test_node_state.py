import pathlib

import git

import zntrack


class DVCOutsNode(zntrack.Node):
    params: float = zntrack.zn.params()
    outs: pathlib.Path = zntrack.dvc.outs(zntrack.nwd / "outs.txt")

    def run(self) -> None:
        with open(self.outs, "w") as f:
            f.write(str(self.params))

    def _custom_open_method(self) -> float:
        """Some read method in some package that can not be changed."""
        with open(self.outs) as f:
            return float(f.read())

    def get_outs(self):
        with self.state.patch_open():
            return self._custom_open_method()


def test_DVCOutsNode(proj_path):
    with zntrack.Project() as project:
        node = DVCOutsNode(params=10)

    project.run()

    # commit all changes
    repo = git.Repo(proj_path)
    repo.git.add(A=True)
    repo.index.commit("save")

    assert node.get_outs() == 10

    with project.create_experiment(queue=False) as exp1:
        node.params = 20

    with project.create_experiment(queue=False) as exp2:
        node.params = 30

    exp1_node = DVCOutsNode.from_rev(rev=exp1.name)
    exp2_node = DVCOutsNode.from_rev(rev=exp2.name)

    assert exp1_node.state.rev == exp1.name
    assert exp2_node.state.rev == exp2.name

    assert exp1_node.get_outs() == 20
    assert exp2_node.get_outs() == 30
