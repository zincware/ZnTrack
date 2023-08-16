"""Collection of ZnTrack example Nodes.

These nodes are primarily used for testing and demonstration purposes.
"""
import pandas as pd

import zntrack


class ParamsToOuts(zntrack.Node):
    """Save params to outs."""

    params = zntrack.params()
    outs = zntrack.outs()

    def run(self) -> None:
        """Save params to outs."""
        self.outs = self.params


class ParamsToMetrics(zntrack.Node):
    """Save params to metrics."""

    params = zntrack.params()
    metrics = zntrack.metrics()

    def run(self) -> None:
        """Save params to metrics."""
        self.metrics = self.params


class WritePlots(zntrack.Node):
    """Generate a plot."""

    plots: pd.DataFrame = zntrack.plots()
    x: list = zntrack.params([1, 2, 3])
    y: list = zntrack.params([4, 5, 6])

    def run(self):
        """Write plots."""
        self.plots = pd.DataFrame({"x": self.x, "y": self.y})


class AddNumbers(zntrack.Node):
    """Add two numbers."""

    a = zntrack.params()
    b = zntrack.params()
    c = zntrack.outs()

    def run(self):
        """Add two numbers."""
        self.c = self.a + self.b


class AddNodes(zntrack.Node):
    """Add two nodes."""

    a: AddNumbers = zntrack.deps()
    b: AddNumbers = zntrack.deps()
    c = zntrack.outs()

    def run(self):
        """Add two nodes."""
        self.c = self.a.c + self.b.c


class AddNodeAttributes(zntrack.Node):
    """Add two node attributes."""

    a: float = zntrack.deps()
    b: float = zntrack.deps()
    c = zntrack.outs()

    def run(self):
        """Add two node attributes."""
        self.c = self.a + self.b


class AddNodeNumbers(zntrack.Node):
    """Add up all 'x.outs' from the dependencies."""

    numbers: list = zntrack.deps()
    sum: int = zntrack.outs()

    def run(self):
        """Add up all 'x.outs' from the dependencies."""
        self.sum = sum(x.outs for x in self.numbers)


class SumNodeAttributes(zntrack.Node):
    """Sum a list of numbers."""

    inputs: list = zntrack.deps()
    shift: int = zntrack.params()
    output: int = zntrack.outs()

    def run(self) -> None:
        """Sum a list of numbers."""
        self.output = sum(self.inputs) + self.shift


class AddOne(zntrack.Node):
    """Add one to the number."""

    number: int = zntrack.deps()
    outs: int = zntrack.outs()

    def run(self) -> None:
        """Add one to the number."""
        self.outs = self.number + 1


class WriteDVCOuts(zntrack.Node):
    """Write an output file."""

    params = zntrack.params()
    outs = zntrack.outs_path(zntrack.nwd / "output.txt")

    def run(self):
        """Write an output file."""
        self.outs.write_text(str(self.params))
