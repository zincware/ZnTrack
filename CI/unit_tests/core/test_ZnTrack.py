import pathlib

import pytest

from zntrack import dvc, zn
from zntrack.core.base import ZnTrack


class ExampleNode:
    def __init__(self):
        self.zntrack = ZnTrack(self)


class FullExampleNode:
    parameter1 = dvc.params()
    parameter2 = dvc.params()
    outs1 = dvc.outs()
    outs2 = dvc.outs()
    result1 = zn.outs()
    result2 = zn.outs()

    def __init__(self):
        self.zntrack = ZnTrack(self)

    def write(self):
        self.parameter1 = "parameter1"
        self.parameter2 = "parameter2"
        self.outs1 = "outs1"
        self.outs2 = "outs2"
        self.result1 = "result1"
        self.result2 = "result2"


@pytest.fixture()
def example_node() -> ExampleNode:
    return ExampleNode()


@pytest.fixture()
def full_example_node() -> FullExampleNode:
    instance = FullExampleNode()
    instance.write()
    return instance


def test_name(example_node):
    assert example_node.zntrack.name == "ExampleNode"


def test_module(example_node):
    assert example_node.zntrack.module == "test_ZnTrack"


def test_stage_name(example_node):
    assert example_node.zntrack.stage_name == "ExampleNode"

    example_node.zntrack.stage_name = "Lorem Ipsum"
    assert example_node.zntrack.stage_name == "Lorem Ipsum"


def test_zn_outs_path(example_node):
    assert example_node.zntrack.zn_outs_path == pathlib.Path("nodes") / "ExampleNode"


def test_update_option_tracker(full_example_node):
    assert len(full_example_node.zntrack.option_tracker.params) == 0
    assert len(full_example_node.zntrack.option_tracker.dvc_options) == 0
    assert len(full_example_node.zntrack.option_tracker.zn_options) == 0
    full_example_node.zntrack.update_option_tracker()
    assert len(full_example_node.zntrack.option_tracker.params) == 2
    assert len(full_example_node.zntrack.option_tracker.dvc_options) == 2
    assert len(full_example_node.zntrack.option_tracker.zn_options) == 2
