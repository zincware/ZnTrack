import zntrack
import pandas as pd
import pytest


class NodeWithPlots(zntrack.Node):
    data = zntrack.dvc.plots(
        "data.csv", x="x", y="y", x_label="x", y_label="y", title="title"
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
