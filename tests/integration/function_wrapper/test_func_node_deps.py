import pathlib

import zntrack
from zntrack.utils import run_dvc_cmd


@zntrack.nodify(outs=pathlib.Path("text.txt"), params={"text": "Lorem Ipsum"})
def write_text(cfg: zntrack.NodeConfig):
    cfg.outs.write_text(cfg.params.text)


class MyNode(zntrack.Node):
    deps: pathlib.Path = zntrack.dvc.deps(pathlib.Path("text.txt"))
    value = zntrack.zn.outs()

    def run(self):
        self.value = self.deps.read_text()


def test_func_node(proj_path):
    write_text()
    with zntrack.Project() as proj:
        MyNode()
    proj.run()

    run_dvc_cmd(["repro"])

    assert pathlib.Path("text.txt").read_text() == "Lorem Ipsum"
    assert MyNode.from_rev().value == "Lorem Ipsum"
    assert MyNode.from_rev().deps == pathlib.Path("text.txt")
