import zntrack
import pandas as pd
import pytest
import yaml


class NodeWithPlotsDVC(zntrack.Node):
    data = zntrack.dvc.plots(
        zntrack.nwd / "data.csv",
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


class NodeWithPlotsZn(zntrack.Node):
    data = zntrack.zn.plots(
        x="x", y="y", x_label="x", y_label="y", title="title", template="linear"
    )

    def run(self) -> None:
        self.data = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

    def get_data(self):
        return self.data


@pytest.mark.parametrize("cls", [NodeWithPlotsDVC, NodeWithPlotsZn])
@pytest.mark.parametrize("eager", [True, False])
def test_NodeWithPlots(proj_path, eager, cls):
    with zntrack.Project() as project:
        node = cls()
    project.run(eager=eager)

    if not eager:
        node.load()
        dvc_dict = yaml.safe_load((proj_path / "dvc.yaml").read_text())

        plots = {
            "x": "x",
            "y": "y",
            "x_label": "x",
            "y_label": "y",
            "title": "title",
            "template": "linear",
        }

        assert (
            dvc_dict["stages"][node.name]["plots"][0][f"nodes/{node.name}/data.csv"]
            == plots
        )

    assert node.get_data()["x"].tolist() == [1, 2, 3]
