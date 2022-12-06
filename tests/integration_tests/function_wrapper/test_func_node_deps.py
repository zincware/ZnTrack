import pathlib

from zntrack import dvc, zn
from zntrack.core.base import Node
from zntrack.core.functions.decorator import NodeConfig, nodify
from zntrack.utils.utils import run_dvc_cmd


@nodify(outs=pathlib.Path("text.txt"), params={"text": "Lorem Ipsum"})
def write_text(cfg: NodeConfig):
    cfg.outs.write_text(cfg.params.text)


class MyNode(Node):
    deps: pathlib.Path = dvc.deps(pathlib.Path("text.txt"))
    value = zn.outs()

    def run(self):
        self.value = self.deps.read_text()


def test_func_node(proj_path):
    write_text()
    MyNode().write_graph()

    run_dvc_cmd(["repro"])

    assert pathlib.Path("text.txt").read_text() == "Lorem Ipsum"
    assert MyNode.load().value == "Lorem Ipsum"
    assert MyNode.load().deps == pathlib.Path("text.txt")
