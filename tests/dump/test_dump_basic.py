import json
import pathlib

import pandas as pd

import zntrack


class MyNode(zntrack.Node):
    parameter: int = zntrack.params()
    parameter_path: str = zntrack.params_path()

    # deps are tested separately

    deps_path: str = zntrack.deps_path()
    deps2_paths: list[pathlib.Path] = zntrack.deps_path()
    outs_path: list[str] = zntrack.outs_path()
    metrics_path: pathlib.Path = zntrack.metrics_path()
    plots_path: list[pathlib.Path] = zntrack.plots_path()

    outs_path_no_cache: list[pathlib.Path] = zntrack.outs_path(cache=False)
    plots_path_no_cache: list[pathlib.Path | str] = zntrack.plots_path(cache=False)
    metrics_path_cache: pathlib.Path = zntrack.metrics_path(cache=True)

    outs: int = zntrack.outs()
    metrics: dict = zntrack.metrics()
    plots: pd.DataFrame = zntrack.plots(y="y")

    outs_no_cache: int = zntrack.outs(cache=False)
    metrics_cache: dict = zntrack.metrics(cache=True)
    plots_no_cache: pd.DataFrame = zntrack.plots(cache=False, y="y")

    def run(self):
        for path in self.deps2_paths:
            with open(path, "w") as f:
                f.write("Lorem ipsum")
        self.metrics_path.write_text(json.dumps({"a": 1}))
        df = pd.DataFrame({"y": [1, 2, 3]})
        for path in self.plots_path:
            df.to_csv(path)
        for path in self.outs_path:
            with open(path, "w") as f:
                f.write("Lorem ipsum")
        for path in self.outs_path_no_cache:
            with open(path, "w") as f:
                f.write("Lorem ipsum")
        for path in self.plots_path_no_cache:
            df.to_csv(path)
        self.metrics_path_cache.write_text(json.dumps({"a": 1}))

        self.outs = 42
        self.metrics = {"a": 1}
        self.plots = df

        self.outs_no_cache = 42
        self.metrics_cache = {"a": 1}
        self.plots_no_cache = df


def test_repro_basic(proj_path):
    with open("parameter.yaml", "w") as f:
        f.write("parameter: 1")
    with open("deps.yaml", "w") as f:
        f.write("deps: 1")
    with open("deps2.yaml", "w") as f:
        f.write("deps2: 1")

    with zntrack.Project() as project:
        node = MyNode(
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
                "no-cache-plots.csv",
            ],
            metrics_path_cache=zntrack.nwd / "metrics-cache.json",
        )

    project.repro()

    assert node.nwd == pathlib.Path("nodes/MyNode")

    assert pathlib.Path("outs.yaml").read_text() == "Lorem ipsum"
    assert (node.nwd / "no-cache-outs.json").read_text() == "Lorem ipsum"

    assert json.loads((node.nwd / "my_metrics.json").read_text()) == {"a": 1}
    assert json.loads((node.nwd / "metrics-cache.json").read_text()) == {"a": 1}

    assert pd.read_csv(node.nwd / "my_plots.csv", index_col=0).equals(
        pd.DataFrame({"y": [1, 2, 3]})
    )
    assert pd.read_csv("no-cache-plots.csv", index_col=0).equals(
        pd.DataFrame({"y": [1, 2, 3]})
    )

    assert json.loads((node.nwd / "outs.json").read_text()) == 42
    assert json.loads((node.nwd / "metrics.json").read_text()) == {"a": 1}
    assert pd.read_csv(node.nwd / "plots.csv", index_col=0).equals(
        pd.DataFrame({"y": [1, 2, 3]})
    )

    assert json.loads((node.nwd / "outs_no_cache.json").read_text()) == 42
    assert json.loads((node.nwd / "metrics_cache.json").read_text()) == {"a": 1}
    assert pd.read_csv(node.nwd / "plots_no_cache.csv", index_col=0).equals(
        pd.DataFrame({"y": [1, 2, 3]})
    )
