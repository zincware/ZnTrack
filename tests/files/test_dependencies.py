import json
import pathlib
import typing as t

import pandas as pd
import yaml

import zntrack

CWD = pathlib.Path(__file__).parent.resolve()


class NodeA1(zntrack.Node):
    metrics_paths: list[pathlib.Path] = zntrack.metrics_path()
    plots_path: list[pathlib.Path] = zntrack.plots_path()
    outs_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "my_output.txt")

    results: int = zntrack.outs()
    metrics: dict = zntrack.metrics()
    plots: pd.DataFrame = zntrack.plots(y="y")

    def run(self):
        pass


class NodeA2(zntrack.Node):
    outs_path: pathlib.Path = zntrack.outs_path(
        zntrack.nwd / "my_output.txt", independent=True
    )
    metrics_paths: list[pathlib.Path] = zntrack.metrics_path(independent=True)
    plots_path: list[pathlib.Path] = zntrack.plots_path(independent=True)

    results: int = zntrack.outs(independent=True)
    metrics: dict = zntrack.metrics(independent=True)
    plots: pd.DataFrame = zntrack.plots(independent=True, y="y")

    def run(self):
        pass


class NodeB(zntrack.Node):
    input: list[int] = zntrack.deps()

    def run(self):
        pass


class NodeC(zntrack.Node):
    deps: zntrack.Node | t.Any = zntrack.deps()

    def run(self):
        pass


class NodeWithProperty(zntrack.Node):
    @property
    def results(self):
        return 1

    def run(self):
        pass


def test_deps(proj_path):
    with zntrack.Project() as project:
        a = NodeA1(
            metrics_paths=[zntrack.nwd / "a.json", zntrack.nwd / "b.json"],
            plots_path=[zntrack.nwd / "p1.csv", zntrack.nwd / "p2.csv"],
        )
        b = NodeA2(
            metrics_paths=[zntrack.nwd / "a.json", zntrack.nwd / "b.json"],
            plots_path=[zntrack.nwd / "p1.csv", zntrack.nwd / "p2.csv"],
        )
        _ = NodeB(input=[a.results, b.results])

    with project.group("dependent"):
        _ = NodeC(deps=a)
        _ = NodeC(deps=a.results)
        _ = NodeC(deps=a.metrics)
        _ = NodeC(deps=a.plots)

    with project.group("independent"):
        _ = NodeC(deps=b)
        _ = NodeC(deps=b.results)
        _ = NodeC(deps=b.metrics)
        _ = NodeC(deps=b.plots)

    with project.group("property"):
        nwp = NodeWithProperty()
        _ = NodeC(deps=nwp.results)
        _ = NodeC(deps=nwp)

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
