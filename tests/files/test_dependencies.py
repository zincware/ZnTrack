import json
import pathlib

import yaml

import zntrack

CWD = pathlib.Path(__file__).parent.resolve()


class NodeA1(zntrack.Node):
    results: int = zntrack.outs()

    def run(self):
        pass


class NodeA2(zntrack.Node):
    results: int = zntrack.outs(independent=True)

    def run(self):
        pass


class NodeB(zntrack.Node):
    input: list[int] = zntrack.deps()

    def run(self):
        pass


def test_deps(proj_path):
    with zntrack.Project() as project:
        a = NodeA1()
        b = NodeA2()
        _ = NodeB(input=[a.results, b.results])

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "dependencies.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "dependencies.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "dependencies.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_deps(None)
