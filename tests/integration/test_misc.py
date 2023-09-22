import pathlib

import yaml
import znflow

import zntrack
from zntrack.utils import config


class NodeWithProperty(zntrack.Node):
    params = zntrack.zn.params(None)

    @property
    def calc(self):
        """This should not change the params if not called."""
        self.params = 42
        return "calc"

    def run(self):
        pass


def test_NodeWithProperty(proj_path):
    with zntrack.Project() as proj:
        node = NodeWithProperty()

    proj.run()

    node.load()
    assert node.params is None


class NodeA(zntrack.Node):
    params1 = zntrack.zn.params(1)


class NodeB(zntrack.Node):
    params2 = zntrack.zn.params(2)


def test_SwitchNode(proj_path):
    with zntrack.Project() as proj:
        NodeA(name="Node")
    proj.run(repro=False)

    params = yaml.safe_load(config.files.params.read_text())
    assert params["Node"] == {"params1": 1}

    with zntrack.Project() as proj:
        NodeB(name="Node")
    proj.run(repro=False)

    params = yaml.safe_load(config.files.params.read_text())
    assert params["Node"] == {"params2": 2}


class CustomModule(zntrack.Node):
    _module_ = "zntrack.nodes"


def test_CustomModule(proj_path):
    with zntrack.Project() as proj:
        CustomModule()
    proj.run(repro=False)

    dvc = yaml.safe_load(config.files.dvc.read_text())
    assert (
        dvc["stages"]["CustomModule"]["cmd"]
        == "zntrack run zntrack.nodes.CustomModule --name CustomModule"
    )
