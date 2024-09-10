import pandas as pd
import pytest
from zntrack.exceptions import InvalidOptionError

import zntrack


class MyNode(zntrack.Node):
    plots: pd.DataFrame = zntrack.plots()
    epochs: int = zntrack.params(10)

    def run(self):
        for epoch in range(self.epochs):
            self.state.extend_plots("plots", {"epoch": epoch})
            assert len(self.plots) == epoch + 1
            assert self.plots["epoch"].iloc[-1] == epoch


class NodeWrongAttr(zntrack.Node):
    metrics: dict = zntrack.metrics()
    def run(self):
        self.state.extend_plots("metrics", {"metric": 1})

class MissingAttr(zntrack.Node):
    def run(self):
        self.state.extend_plots("plots", {"metric": 1})


def test_extend_plots():
    MyNode().run()

def test_extend_plots_wrong_attr():
    with pytest.raises(InvalidOptionError):
        NodeWrongAttr().run()

def test_extend_plots_missing_attr():
    with pytest.raises(InvalidOptionError):
        MissingAttr().run()