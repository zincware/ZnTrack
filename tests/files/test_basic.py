import pathlib

import pandas as pd

import zntrack


class MyNode(zntrack.Node):
    parameter: int = zntrack.params()
    parameter_path: str = zntrack.params_path()

    # deps are tested separately

    deps_path: str = zntrack.deps_path()
    outs_path: list[str] = zntrack.outs_path()
    metrics_path: pathlib.Path = zntrack.metrics_path()
    plots_path: list[pathlib.Path] = zntrack.plots_path()

    outs: int = zntrack.outs()
    metrics: dict = zntrack.metrics()
    plots: pd.DataFrame = zntrack.plots()


CWD = pathlib.Path(__file__).parent.resolve()


def test_basic():
    with zntrack.Project() as project:
        _ = MyNode(
            parameter=1,
            parameter_path="parameter.yaml",
            deps_path="deps.yaml",
            outs_path=["outs.yaml"],
            metrics_path=zntrack.nwd / "my_metrics.json",
            plots_path=[zntrack.nwd / "my_plots.csv"],
        )

    # dvc stage add --name MyNode --force --params parameter.yaml: --outs nodes/MyNode/my_plots.csv --params params.yaml:MyNode --metrics-no-cache nodes/MyNode/metrics.json --outs nodes/MyNode/outs.json --metrics nodes/MyNode/my_metrics.json --outs outs.yaml --deps deps.yaml --metrics-no-cache nodes/MyNode/node-meta.json zntrack run test_basic.MyNode --name MyNode
    
    # TODO: outs
    # TODO: metrics
    # TODO: plots

    project.build()

    assert (CWD / "zntrack_config" / "basic.json").read_text() == (
        proj_path / "zntrack.json"
    ).read_text()
    assert (CWD / "dvc_config" / "basic.yaml").read_text() == (
        proj_path / "dvc.yaml"
    ).read_text()
    assert (CWD / "params_config" / "basic.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()
