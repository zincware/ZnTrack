import pathlib

import yaml

import zntrack


class NodeWithOuts(zntrack.Node):
    def run(self):
        pass


class DependentNode(zntrack.Node):
    deps = zntrack.zn.deps()

    def run(self):
        pass


def test_DependentNode(proj_path):
    with zntrack.Project() as proj:
        a = NodeWithOuts()
        b = DependentNode(deps=a)

    proj.run(repro=False)

    dvc_yaml = yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (
        dvc_yaml["stages"]["DependentNode"]["cmd"]
        == "zntrack run test_zn_deps.DependentNode --name DependentNode"
    )
    assert dvc_yaml["stages"]["DependentNode"]["deps"] == ["nodes/NodeWithOuts/uuid"]
