import json
import pathlib

import pandas as pd
import yaml

import zntrack


class MyNode(zntrack.Node):
    parameter: int = zntrack.params()
    parameter_path: str = zntrack.params_path()

    # deps are tested separately

    deps_path: str = zntrack.deps_path()
    deps2_paths: list[pathlib.Path] = zntrack.deps_path()
    outs_path: list[str] = zntrack.outs_path(cache=True)
    metrics_path: pathlib.Path = zntrack.metrics_path(cache=False)
    plots_path: list[pathlib.Path] = zntrack.plots_path(cache=True)

    outs_path_no_cache: list[pathlib.Path] = zntrack.outs_path(cache=False)
    plots_path_no_cache: list[pathlib.Path | str] = zntrack.plots_path(cache=False)
    metrics_path_cache: pathlib.Path = zntrack.metrics_path(cache=True)

    outs: int = zntrack.outs()
    metrics: dict = zntrack.metrics(cache=False)
    plots: pd.DataFrame = zntrack.plots(y="y")

    outs_no_cache: int = zntrack.outs(cache=False)
    metrics_cache: dict = zntrack.metrics(cache=True)
    plots_no_cache: pd.DataFrame = zntrack.plots(cache=False, y="y")


CWD = pathlib.Path(__file__).parent.resolve()


def test_basic(proj_path):
    with zntrack.Project() as project:
        _ = MyNode(
            parameter=1,
            parameter_path="parameter.yaml",
            deps_path="deps.yaml",
            deps2_paths=[pathlib.Path("deps2.yaml")],
            outs_path=["outs.yaml"],
            metrics_path=zntrack.nwd / "my_metrics.json",
            plots_path=[zntrack.nwd / "my_plots.csv"],
            outs_path_no_cache=[zntrack.nwd / "no-cache-outs.json"],
            plots_path_no_cache=[
                zntrack.nwd / "no-cache-plots.csv",
                "no-cache-plots.json",
            ],
            metrics_path_cache=zntrack.nwd / "metrics-cache.json",
        )

    project.build()

    assert json.loads((CWD / "zntrack_config" / "basic.json").read_text()) == json.loads(
        (proj_path / "zntrack.json").read_text()
    )
    assert yaml.safe_load(
        (CWD / "dvc_config" / "basic.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "basic.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_basic(None)
