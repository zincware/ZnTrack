import zntrack
import pandas as pd 


class MyNode(zntrack.Node):
    plots: pd.DataFrame = zntrack.plots()
    epochs: int = zntrack.params(10)

    def run(self):
        for epoch in range(self.epochs):
            self.state.extend_plots("plots", {"epoch": epoch})
            assert len(self.plots) == epoch + 1
            assert self.plots["epoch"].iloc[-1] == epoch

def test_extend_plots():
    MyNode().run()

