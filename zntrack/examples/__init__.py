"""Collection of ZnTrack example Nodes.

These nodes are primarily used for testing and demonstration purposes.
"""

import json
import pathlib
import random
import typing as t

import pandas as pd

import zntrack


class ReadFile(zntrack.Node):
    """Read a file."""

    path: pathlib.Path = zntrack.deps_path()
    content: str = zntrack.outs()

    def run(self):
        """Read a file."""
        self.content = self.path.read_text()


class ParamsToOuts(zntrack.Node):
    """Save params to outs."""

    params: t.Any = zntrack.params()
    outs: t.Any = zntrack.outs()

    def run(self) -> None:
        """Save params to outs."""
        self.outs = self.params

    def join(self) -> None:
        """Join the results."""
        self.outs = "-".join(self.params)


class ParamsToMetrics(zntrack.Node):
    """Save params to metrics."""

    params: dict = zntrack.params()
    metrics: dict = zntrack.metrics()

    def run(self) -> None:
        """Save params to metrics."""
        self.metrics = self.params

    def __run_note__(self) -> str:
        """Markdown style run note."""
        return "This is a test run note."


class DepsToMetrics(zntrack.Node):
    """Save params to metrics."""

    deps: dict = zntrack.deps()
    metrics: dict = zntrack.metrics()

    def run(self) -> None:
        """Save params to metrics."""
        self.metrics = self.deps


class WritePlots(zntrack.Node):
    """Generate a plot."""

    plots: pd.DataFrame = zntrack.plots(x="x", y="y")
    x: list = zntrack.params(default_factory=lambda: [1, 2, 3])
    y: list = zntrack.params(default_factory=lambda: [4, 5, 6])

    def run(self):
        """Write plots."""
        self.plots = pd.DataFrame({"x": self.x, "y": self.y})


class AddNumbers(zntrack.Node):
    """Add two numbers."""

    a: float = zntrack.params()
    b: float = zntrack.params()
    c: float = zntrack.outs()

    def run(self):
        """Add two numbers."""
        self.c = self.a + self.b


class AddNumbersProperty(zntrack.Node):
    """Add two numbers."""

    a: float = zntrack.params()
    b: float = zntrack.params()

    @property
    def c(self):
        """Add two numbers."""
        return self.a + self.b


class AddNodes(zntrack.Node):
    """Add two nodes."""

    a: AddNumbers = zntrack.deps()
    b: AddNumbers = zntrack.deps()
    c: float = zntrack.outs()

    def run(self):
        """Add two nodes."""
        self.c = self.a.c + self.b.c


class AddNodes2(zntrack.Node):
    """Add two nodes."""

    a: ParamsToOuts = zntrack.deps()
    b: ParamsToOuts = zntrack.deps()
    c: float = zntrack.outs()

    def run(self):
        """Add two nodes."""
        self.c = self.a.outs + self.b.outs


class AddNodeAttributes(zntrack.Node):
    """Add two node attributes."""

    a: float = zntrack.deps()
    b: float = zntrack.deps()
    c: float = zntrack.outs()

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

    inputs: list[float | int] = zntrack.deps()
    shift: int | float = zntrack.params()
    output: int | float = zntrack.outs()

    def run(self) -> None:
        """Sum a list of numbers."""
        self.output = sum(self.inputs) + self.shift


class SumNodeAttributesToMetrics(zntrack.Node):
    """Sum a list of numbers."""

    inputs: list[float | int] = zntrack.deps()
    shift: int | float = zntrack.params()
    metrics: dict[str, int | float] = zntrack.metrics()

    def run(self) -> None:
        """Sum a list of numbers."""
        self.metrics = {"value": sum(self.inputs) + self.shift}


class AddOne(zntrack.Node):
    """Add one to the number."""

    number: int = zntrack.deps()
    outs: int = zntrack.outs()

    def run(self) -> None:
        """Add one to the number."""
        self.outs = self.number + 1


class WriteDVCOuts(zntrack.Node):
    """Write an output file."""

    params: t.Any = zntrack.params()
    outs: pathlib.Path | str = zntrack.outs_path(zntrack.nwd / "output.txt")

    def run(self):
        """Write an output file."""
        pathlib.Path(self.outs).write_text(str(self.params))

    def get_outs_content(self):
        """Get the output file."""
        with self.state.use_tmp_path():
            return pathlib.Path(self.outs).read_text()


class WriteDVCOutsSequence(zntrack.Node):
    """Write an output file."""

    params: list = zntrack.params()
    outs: t.Union[list, tuple, set, dict] = zntrack.outs_path()

    def run(self):
        """Write an output file."""
        for value, path in zip(self.params, self.outs):
            pathlib.Path(path).write_text(str(value))

    def get_outs_content(self):
        """Get the output file."""
        data = []
        with self.state.use_tmp_path():
            for path in self.outs:
                data.append(pathlib.Path(path).read_text())
        return data


class WriteDVCOutsPath(zntrack.Node):
    """Write an output file."""

    params: t.Any = zntrack.params()
    outs: pathlib.Path | str = zntrack.outs_path(zntrack.nwd / "data")

    def run(self):
        """Write an output file."""
        pathlib.Path(self.outs).mkdir(parents=True, exist_ok=True)
        (pathlib.Path(self.outs) / "file.txt").write_text(str(self.params))

    def get_outs_content(self):
        """Get the output file."""
        with self.state.use_tmp_path():
            try:
                return (pathlib.Path(self.outs) / "file.txt").read_text()
            except FileNotFoundError:
                files = list(pathlib.Path(self.outs).iterdir())
                raise ValueError(f"Expected {self.outs } file, found {files}.")


class WriteMultipleDVCOuts(zntrack.Node):
    """Write an output file."""

    params: t.Any = zntrack.params()
    outs1: pathlib.Path = zntrack.outs_path(zntrack.nwd / "output.txt")
    outs2: pathlib.Path = zntrack.outs_path(zntrack.nwd / "output2.txt")
    outs3: pathlib.Path = zntrack.outs_path(zntrack.nwd / "data")

    def run(self):
        """Write an output file."""
        pathlib.Path(self.outs1).write_text(str(self.params[0]))
        pathlib.Path(self.outs2).write_text(str(self.params[1]))
        pathlib.Path(self.outs3).mkdir(parents=True, exist_ok=True)
        (pathlib.Path(self.outs3) / "file.txt").write_text(str(self.params[2]))

    def get_outs_content(self) -> t.Tuple[str, str, str]:
        """Get the output file."""
        with self.state.use_tmp_path():
            outs1_content = pathlib.Path(self.outs1).read_text()
            outs2_content = pathlib.Path(self.outs2).read_text()
            outs3_content = (pathlib.Path(self.outs3) / "file.txt").read_text()
            return outs1_content, outs2_content, outs3_content


class ComputeRandomNumber(zntrack.Node):
    """Compute a random number."""

    params_file: str = zntrack.params_path()

    number: float = zntrack.outs()

    # def _post_init_(self):
    #     super()._post_init_()
    #     self.params_file = pathlib.Path(self.params_file)
    #     raise ValueError("This is a test exception, simulating killing the Node.")

    def run(self):
        """Compute a random number."""
        self.number = self.get_random_number()

    def get_random_number(self):
        """Compute a random number."""
        params = json.loads(pathlib.Path(self.params_file).read_text())
        random.seed(params["seed"])
        return random.randint(params["min"], params["max"])

    def write_params(self, min, max, seed):
        """Write params to file."""
        pathlib.Path(self.params_file).write_text(
            json.dumps({"min": min, "max": max, "seed": seed})
        )


class ComputeRandomNumberWithParams(zntrack.Node):
    """Compute a random number."""

    min: int = zntrack.params()
    max: int = zntrack.params()
    seed: int = zntrack.params()

    number: float = zntrack.outs()

    def run(self):
        """Compute a random number."""
        self.number = self.get_random_number()

    def get_random_number(self):
        """Compute a random number."""
        random.seed(self.seed)
        return random.randint(self.min, self.max)


class ComputeRandomNumberNamed(ComputeRandomNumber):
    """Same as ComputeRandomNumber but with a custom name."""

    _name_ = "custom_ComputeRandomNumber"


class SumRandomNumbers(zntrack.Node):
    """Sum a list of random numbers."""

    numbers: t.List[ComputeRandomNumber] = zntrack.deps()
    result: int = zntrack.outs()

    def run(self):
        """Sum a list of random numbers."""
        self.result = sum(x.get_random_number() for x in self.numbers)


class SumRandomNumbersNamed(SumRandomNumbers):
    """Same as SumRandomNumbers but with a custom name."""

    _name_ = "custom_SumRandomNumbers"


class NodeWithRestart(zntrack.Node):
    """Node that restarts."""

    start: int = zntrack.params()
    raise_exception_until: int = zntrack.params(0)

    count: int = zntrack.outs()

    def run(self) -> None:
        """Run the node.

        Increments the count by one, for each run.
        Check that the restart flag is set.
        """
        self.count = self.start + self.state.run_count
        if self.state.run_count > 1:
            assert self.state.restarted
        if self.state.run_count < self.raise_exception_until:
            raise ValueError("This is a test exception, simulating killing the Node.")


class OptionalDeps(zntrack.Node):
    """Node with optional dependencies."""

    value: float = zntrack.deps(None)
    result: float = zntrack.outs()

    def run(self) -> None:
        """Run the node."""
        self.result = self.value or 0.0
