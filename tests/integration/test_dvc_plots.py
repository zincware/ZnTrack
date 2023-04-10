import zntrack
import pandas as pd
import pytest
import yaml


class NodeWithPlots(zntrack.Node):
    data = zntrack.dvc.plots(
        "data.csv",
        x="x",
        y="y",
        x_label="x",
        y_label="y",
        title="title",
        template="linear",
    )

    def run(self) -> None:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        df.to_csv(self.data)

    def get_data(self):
        return pd.read_csv(self.data)


@pytest.mark.parametrize("eager", [True, False])
def test_NodeWithPlots(proj_path, eager):
    with zntrack.Project() as project:
        node = NodeWithPlots()
    project.run(eager=eager)

    assert node.get_data()["x"].tolist() == [1, 2, 3]
    if not eager:
        dvc_dict = yaml.safe_load((proj_path / "dvc.yaml").read_text())

        plots = {
            "x": "x",
            "y": "y",
            "x_label": "x",
            "y_label": "y",
            "title": "title",
            "template": "linear",
        }

        assert dvc_dict["stages"]["NodeWithPlots"]["plots"][0]["data.csv"] == plots
