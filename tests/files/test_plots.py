import json
import pathlib

import pandas as pd
import yaml

import zntrack
import zntrack.group

CWD = pathlib.Path(__file__).parent.resolve()


class Plotting(zntrack.Node):
    a: pd.DataFrame = zntrack.plots(
        y="loss",
        x="epoch",
        x_label="Epoch",
        y_label="Loss",
        template="plotly_dark",
        title="Loss over Epochs",
    )


def test_plotting(proj_path):
    with zntrack.Project() as proj:
        Plotting()

    proj.build()

    assert json.loads((CWD / "zntrack_config" / "plots.json").read_text()) == json.loads(
        (proj_path / "zntrack.json").read_text()
    )
    assert yaml.safe_load(
        (CWD / "dvc_config" / "plots.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "plots.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_plotting("")
