import json
import os
import pathlib

import pytest
import yaml

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


class ExampleOnlyParams:
    params1 = dvc.params()
    params2 = dvc.params()

    def __init__(self):
        self.zntrack = ZnTrack(self)

    def write(self):
        self.params1 = "Lorem"
        self.params2 = "Ipsum"


class ExampleOnlyDVCOuts:
    params1 = dvc.outs()
    params2 = dvc.outs()

    def __init__(self):
        self.zntrack = ZnTrack(self)

    def write(self):
        self.params1 = "Lorem"
        self.params2 = "Ipsum"


class ExampleOnlyZnOuts:
    params1 = zn.outs()
    params2 = zn.outs()

    def __init__(self):
        self.zntrack = ZnTrack(self)

    def write(self):
        self.params1 = "Lorem"
        self.params2 = "Ipsum"


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


def test_python_interpreter(example_node):
    assert example_node.zntrack.python_interpreter in ["python", "python3"]


def test_update_option_tracker(full_example_node):
    assert len(full_example_node.zntrack.option_tracker.params) == 0
    assert len(full_example_node.zntrack.option_tracker.dvc_options) == 0
    assert len(full_example_node.zntrack.option_tracker.zn_options) == 0
    full_example_node.zntrack.update_option_tracker()
    assert len(full_example_node.zntrack.option_tracker.params) == 2
    assert len(full_example_node.zntrack.option_tracker.dvc_options) == 2
    assert len(full_example_node.zntrack.option_tracker.zn_options) == 2


def test_affected_files(full_example_node):
    full_example_node.zntrack.update_option_tracker()
    assert full_example_node.zntrack.affected_files == {
        pathlib.Path("nodes", "FullExampleNode", "outs.json"),
        pathlib.Path("outs1"),
        pathlib.Path("outs2"),
    }


def test_update_twice(full_example_node):
    full_example_node.zntrack.update_option_tracker()
    full_example_node.zntrack.update_option_tracker()
    assert len(full_example_node.zntrack.option_tracker.params) == 2
    assert len(full_example_node.zntrack.option_tracker.dvc_options) == 2
    assert len(full_example_node.zntrack.option_tracker.zn_options) == 2


def test_save_params(tmp_path):
    os.chdir(tmp_path)

    example = ExampleOnlyParams()
    example.write()

    example.zntrack.update_option_tracker()
    example.zntrack._save_params()

    with example.zntrack.params_file.open("r") as f:
        full_params_file = yaml.safe_load(f)

    assert full_params_file["ExampleOnlyParams"] == {
        "params1": "Lorem",
        "params2": "Ipsum",
    }

    # save if the file already exists
    example.zntrack._save_params()

    with example.zntrack.params_file.open("r") as f:
        full_params_file = yaml.safe_load(f)

    assert full_params_file["ExampleOnlyParams"] == {
        "params1": "Lorem",
        "params2": "Ipsum",
    }


def test_save_dvc_options(tmp_path):
    os.chdir(tmp_path)

    example = ExampleOnlyDVCOuts()
    example.write()

    example.zntrack.update_option_tracker()
    example.zntrack._save_dvc_options()

    zntrack_file = json.loads(example.zntrack.zntrack_file.read_text())
    assert zntrack_file["ExampleOnlyDVCOuts"] == {"params1": "Lorem", "params2": "Ipsum"}


def test_save_zn_options(tmp_path):
    os.chdir(tmp_path)

    example = ExampleOnlyZnOuts()
    example.write()

    example.zntrack.update_option_tracker()
    example.zntrack._save_zn_options()

    zn_outs = json.loads(
        pathlib.Path("nodes", "ExampleOnlyZnOuts", "outs.json").read_text()
    )
    assert zn_outs == {"params1": "Lorem", "params2": "Ipsum"}
