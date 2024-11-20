import json
import pathlib

import yaml
import znflow

import zntrack.config

CWD = pathlib.Path(__file__).parent.resolve()


class NodeA(zntrack.Node):
    results: int = zntrack.outs()

    def run(self):
        pass


class NodeB(zntrack.Node):
    input: int = zntrack.deps()

    def run(self):
        pass


def test_deps(proj_path):
    with zntrack.Project() as project:
        a1 = NodeA()
        a2 = NodeA()
        b = NodeB(input=a1.results + a2.results)

    assert isinstance(b.input, znflow.CombinedConnections)
    assert b.input.connections[0].instance == a1
    assert b.input.connections[1].instance == a2

    assert a1.results is zntrack.config.NOT_AVAILABLE
    assert a2.results is zntrack.config.NOT_AVAILABLE

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "combined_dependencies.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "combined_dependencies.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "combined_dependencies.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_deps(None)
