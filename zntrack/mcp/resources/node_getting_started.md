```py
import zntrack
from pathlib import Path

class MyNode(zntrack.Node):
    parameter: dict = zntrack.params()
    output: Path = zntrack.outs_path(zntrack.nwd / "file.txt")

    def run(self) -> None:
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text(str(self.parameter))
```

Options include
- `zntrack.deps()` for dependencies to other nodes.
- `zntrack.deps_path` for dependencies to files.
- `zntrack.params` for parameters.
- `zntrack.params_path()` for parameter files (yaml / json)
- `zntrack.outs_path()` for output files.
- `zntrack.outs()` for outputs that are not files.
- `zntrack.metrics()` dict output.
- `zntrack.metrics_path()` for metrics files.

Special directory options include
- `zntrack.nwd` for the node working directory.
