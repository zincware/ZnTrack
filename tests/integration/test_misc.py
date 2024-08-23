import yaml

import zntrack
from zntrack import config


class NodeWithProperty(zntrack.Node):
    params: int = zntrack.params(None)

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

    proj.build()
    proj.run()

    node = node.from_rev()
    assert node.params is None


class NodeA(zntrack.Node):
    params1: int = zntrack.params(1)


class NodeB(zntrack.Node):
    params2: int = zntrack.params(2)


def test_SwitchNode(proj_path):
    with zntrack.Project() as proj:
        NodeA(name="Node")
    proj.build()

    params = yaml.safe_load(config.PARAMS_FILE_PATH.read_text())
    assert params["Node"] == {"params1": 1}

    with zntrack.Project() as proj:
        NodeB(name="Node")
    proj.build()

    params = yaml.safe_load(config.PARAMS_FILE_PATH.read_text())
    assert params["Node"] == {"params2": 2}


class CustomModule(zntrack.Node):
    _module_ = "package.module"


def test_CustomModule(proj_path):
    with zntrack.Project() as proj:
        CustomModule()
    proj.build()

    dvc = yaml.safe_load(config.DVC_FILE_PATH.read_text())
    assert (
        dvc["stages"]["CustomModule"]["cmd"]
        == "zntrack run package.module.CustomModule --name CustomModule"
    )
