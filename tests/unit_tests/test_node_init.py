"""Creating a Node with invalid parameters should raise an error."""

import pathlib

import pandas as pd
import pytest

import zntrack


class MyNode(zntrack.Node):
    # required
    parameter: int = zntrack.params()
    parameter_path: str = zntrack.params_path()

    deps_path: str = zntrack.deps_path()
    outs_path: str = zntrack.outs_path()
    metrics_path: str = zntrack.metrics_path()
    plots_path: str = zntrack.plots_path()

    # optional
    opt_parameter: int = zntrack.params(1)
    opt_parameter_path: str = zntrack.params_path("parameter.yaml")

    opt_deps_path: str = zntrack.deps_path("deps.yaml")
    opt_outs_path: str = zntrack.outs_path("outs.yaml")
    opt_metrics_path: str = zntrack.metrics_path("my_metrics.json")
    opt_plots_path: str = zntrack.plots_path("my_plots.csv")

    # not allowed
    outs: int = zntrack.outs()
    metrics: dict = zntrack.metrics()
    plots: pd.DataFrame = zntrack.plots(y="y")


class SimpleMyNode(zntrack.Node):
    outs_path_a: str = zntrack.outs_path()
    outs_path_b: str = zntrack.outs_path()

    def run(self):
        pathlib.Path(self.outs_path_a).write_text("a")
        pathlib.Path(self.outs_path_b).write_text("b")


def test_init():
    with pytest.raises(TypeError):
        MyNode()  # missing required parameters

    # works
    MyNode(
        parameter=1,
        parameter_path="parameter.yaml",
        deps_path="deps.yaml",
        outs_path="outs.yaml",
        metrics_path="my_metrics.json",
        plots_path="my_plots.csv",
    )
    # works with optional
    MyNode(
        parameter=1,
        parameter_path="parameter.yaml",
        deps_path="deps.yaml",
        outs_path="outs.yaml",
        metrics_path="my_metrics.json",
        plots_path="my_plots.csv",
        opt_parameter=1,
        opt_parameter_path="parameter_1.yaml",
        opt_deps_path="deps_1.yaml",
        opt_outs_path="outs_1.yaml",
        opt_metrics_path="my_metrics_1.json",
        opt_plots_path="my_plots_1.csv",
    )

    # fails with not allowed
    with pytest.raises(TypeError):
        MyNode(
            parameter=1,
            parameter_path="parameter.yaml",
            deps_path="deps.yaml",
            outs_path="outs.yaml",
            metrics_path="my_metrics.json",
            plots_path="my_plots.csv",
            # not allowed
            outs=1,
        )
    with pytest.raises(TypeError):
        MyNode(
            parameter=1,
            parameter_path="parameter.yaml",
            deps_path="deps.yaml",
            outs_path="outs.yaml",
            metrics_path="my_metrics.json",
            plots_path="my_plots.csv",
            # not allowed
            metrics={},
        )
    with pytest.raises(TypeError):
        MyNode(
            parameter=1,
            parameter_path="parameter.yaml",
            deps_path="deps.yaml",
            outs_path="outs.yaml",
            metrics_path="my_metrics.json",
            plots_path="my_plots.csv",
            # not allowed
            plots=pd.DataFrame(),
        )


@pytest.mark.xfail(
    reason="Duplicate outs are currently filtered, but should raise an error."
)
def test_duplicate_outs_paths(proj_path):
    with pytest.raises(ValueError):
        with zntrack.Project() as proj:
            SimpleMyNode(
                outs_path_a="file.txt",
                outs_path_b="file.txt",
            )
        proj.build()


if __name__ == "__main__":
    test_duplicate_outs_paths("proj_path")
