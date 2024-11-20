"""Test that the dataclass post_init works properly."""

import zntrack


class NodeWithPostInit(zntrack.Node):
    def __post_init__(self):
        self.value = 42

    def run(self):
        pass


def test_create_node_with_post_init_plain(proj_path):
    node = NodeWithPostInit()
    assert node.value == 42


def test_create_node_with_post_init_project(proj_path):
    project = zntrack.Project()
    with project:
        node = NodeWithPostInit()
    assert node.value == 42


def test_create_node_with_post_init_from_rev(proj_path):
    node = NodeWithPostInit.from_rev()
    assert node.value == 42


def test_run_node_with_post_init(proj_path):
    project = zntrack.Project()
    with project:
        node = NodeWithPostInit()
    project.run()
    assert node.value == 42


def test_repro_node_with_post_init(proj_path):
    project = zntrack.Project()
    with project:
        node = NodeWithPostInit()
    project.repro()
    assert node.value == 42
    assert NodeWithPostInit.from_rev().value == 42
