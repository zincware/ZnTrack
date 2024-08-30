import json
import subprocess

import zntrack


class MetricsNode(zntrack.Node):
    n: int = zntrack.params()

    metrics: dict = zntrack.metrics()

    def run(self):
        self.metrics = {"n": self.n}


def test_simple_metrics(proj_path):
    with zntrack.Project() as proj:
        node = MetricsNode(n=10)

    proj.build()
    subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)

    with open(node.nwd / "metrics.json") as f:
        metrics = json.load(f)

    assert isinstance(metrics, dict)
    assert metrics["n"] == 10
    assert len(metrics) == 1

    assert isinstance(node.metrics, dict)
    assert node.metrics["n"] == 10
    assert len(node.metrics) == 1

    # create a new instance (lazy loading)
    node = node.from_rev()
    assert isinstance(node.metrics, dict)
    assert node.metrics["n"] == 10
    assert len(node.metrics) == 1
