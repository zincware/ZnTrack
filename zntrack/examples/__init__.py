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


class AddNodeNumbers(zntrack.Node):
    """Add up all 'x.outs' from the dependencies."""

    numbers: list = zntrack.zn.deps()
    sum: int = zntrack.zn.outs()

    def run(self):
        """Add up all 'x.outs' from the dependencies."""
        self.sum = sum(x.outs for x in self.numbers)


class SumNodeAttributes(zntrack.Node):
    """Sum a list of numbers."""

    inputs: list = zntrack.zn.deps()
    shift: int = zntrack.zn.params()
    output: int = zntrack.zn.outs()

    def run(self) -> None:
        """Sum a list of numbers."""
        self.output = sum(self.inputs) + self.shift


class AddOne(zntrack.Node):
    """Add one to the number."""

    number: int = zntrack.zn.deps()
    outs: int = zntrack.zn.outs()

    def run(self) -> None:
        """Add one to the number."""
        self.outs = self.number + 1
