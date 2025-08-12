import json
import pathlib
import typing as t

import yaml

import zntrack

CWD = pathlib.Path(__file__).parent.resolve()


class MyNode(zntrack.Node):
    deps_path: t.Union[list[t.Union[str, None]], None] = zntrack.deps_path()
    params_path: t.Union[list[t.Union[str, None]], None] = zntrack.params_path()
    outs_path: t.Union[list[t.Union[str, None]], None] = zntrack.outs_path()
    metrics_path: t.Union[list[t.Union[str, None]], None] = zntrack.metrics_path()
    plots_path: t.Union[list[t.Union[str, None]], None] = zntrack.plots_path()

    def run(self):
        pass


def test_x_path_none(proj_path):
    project = zntrack.Project()

    with project:
        _ = MyNode(
            deps_path=None,
            params_path=None,
            outs_path=None,
            metrics_path=None,
            plots_path=None,
        )
        _ = MyNode(
            deps_path=[None],
            params_path=[None],
            outs_path=[None],
            metrics_path=[None],
            plots_path=[None],
        )

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "x_path_none.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "x_path_none.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "x_path_none.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()
