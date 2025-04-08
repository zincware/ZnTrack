import random

import numpy as np
import pytest

import zntrack.examples


@pytest.mark.benchmark(group="node-count")
@pytest.mark.parametrize("count", np.linspace(10, 10000, 10, dtype=int).tolist())
# @pytest.mark.parametrize("count", [10, 50, 100, 500, 1_000, 5_000, 10_000])
def test_node_count(benchmark, count, tmp_path):
    """
    Benchmark the number of nodes in a graph.
    """

    def _build():
        project = zntrack.Project()
        with project:
            for _ in range(count):
                zntrack.examples.AddNumbers(
                    a=random.randint(1, 1000),
                    b=random.randint(1, 1000),
                )
        project.build()

    benchmark(_build)


@pytest.mark.benchmark(group="edge-count")
@pytest.mark.parametrize("count", np.linspace(10, 500, 10, dtype=int).tolist())
def test_connections(benchmark, count, tmp_path):
    """
    Benchmark the number of connections in a graph.
    """

    # TODO: there might be a difference in performance depending on
    # the longest_path in the DAG or even the degree per node.

    def _build():
        project = zntrack.Project()
        assert count < 1000, "Count must be less than 1000"
        initial_nodes = 1000 - count
        nodes = []
        with project:
            for _ in range(initial_nodes):
                nodes.append(
                    zntrack.examples.AddNumbers(
                        a=random.randint(1, 1000),
                        b=random.randint(1, 1000),
                    )
                )
            for _ in range(count):
                zntrack.examples.AddNodes(
                    a=random.choice(nodes),
                    b=None,
                )

        assert len(project.nodes) == 1000
        assert len(project.edges) == count

        project.build()

    benchmark(_build)
