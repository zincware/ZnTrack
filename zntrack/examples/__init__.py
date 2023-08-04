"""Collection of ZnTrack example Nodes.

These nodes are primarily used for testing and demonstration purposes.
"""
import pandas as pd

import zntrack


class ParamsToOuts(zntrack.Node):
    """Save params to outs."""

    params = zntrack.zn.params()
    outs = zntrack.zn.outs()

    def run(self) -> None:
        """Save params to outs."""
        self.outs = self.params


class ParamsToMetrics(zntrack.Node):
    """Save params to metrics."""

    params = zntrack.zn.params()
    metrics = zntrack.zn.metrics()

    def run(self) -> None:
        """Save params to metrics."""
        self.metrics = self.params


class WritePlots(zntrack.Node):
    """Generate a plot."""

    plots: pd.DataFrame = zntrack.zn.plots()
    x: list = zntrack.zn.params([1, 2, 3])
    y: list = zntrack.zn.params([4, 5, 6])

    def run(self):
        """Write plots."""
        self.plots = pd.DataFrame({"x": self.x, "y": self.y})


class AddNumbers(zntrack.Node):
    """Add two numbers."""

    a = zntrack.zn.params()
    b = zntrack.zn.params()
    c = zntrack.zn.outs()

    def run(self):
        """Add two numbers."""
        self.c = self.a + self.b


class AddNodes(zntrack.Node):
    """Add two nodes."""

    a: AddNumbers = zntrack.zn.deps()
    b: AddNumbers = zntrack.zn.deps()
    c = zntrack.zn.outs()

    def run(self):
        """Add two nodes."""
        self.c = self.a.c + self.b.c


class AddNodeAttributes(zntrack.Node):
    """Add two node attributes."""

    a: float = zntrack.zn.deps()
    b: float = zntrack.zn.deps()
    c = zntrack.zn.outs()

    def run(self):
        """Add two node attributes."""
        self.c = self.a + self.b
