import pathlib
import subprocess

import pytest

from zntrack import Node, utils, zn
from zntrack.interface import DVCInterface


class HelloWorld(Node):
    outputs = zn.outs()
    inputs = zn.params()

    def __init__(self, inputs=None, **kwargs):
        super(HelloWorld, self).__init__(**kwargs)
        self.inputs = inputs

    def run(self):
        self.outputs = self.inputs


@pytest.fixture()
def single_experiment_path(proj_path):
    HelloWorld(inputs=1).write_graph()
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Init"])

    utils.run_dvc_cmd(["repro"])


@pytest.fixture()
def multi_experiment_path(proj_path):
    HelloWorld(inputs=1).write_graph()
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Init"])

    utils.run_dvc_cmd(["repro"])

    HelloWorld(inputs=2).write_graph()
    utils.run_dvc_cmd(["exp", "run", "-n", "Test02"])
    HelloWorld(inputs=3).write_graph()
    utils.run_dvc_cmd(["exp", "run", "-n", "Test03"])


@pytest.fixture()
def loaded_dvc_interface(single_experiment_path) -> DVCInterface:
    return DVCInterface()


def test_experiments(loaded_dvc_interface):
    """Check that loading works and look for the default workspace environment"""
    assert "workspace" in loaded_dvc_interface.experiments


def test_exp_list(loaded_dvc_interface):
    assert loaded_dvc_interface.exp_list[0].name in ["master", "main"]
    assert len(loaded_dvc_interface.exp_list) == 1


def test__reset(loaded_dvc_interface):
    loaded_dvc_interface._reset()
    assert loaded_dvc_interface.exp_list[0].name in ["master", "main"]


def test_load_files_into_directory(multi_experiment_path):
    """Test for specific experiments"""
    interface = DVCInterface()
    interface.load_files_into_directory(
        files=["nodes/HelloWorld/outs.json"], experiments=["Test02", "Test03"]
    )
    assert pathlib.Path("experiments/Test02/outs.json").exists()
    assert pathlib.Path("experiments/Test03/outs.json").exists()


def test_load_files_into_directory_all_exp(multi_experiment_path):
    """Test for all experiments"""
    interface = DVCInterface()
    interface.load_files_into_directory(files=["nodes/HelloWorld/outs.json"])
    assert pathlib.Path("experiments/Test02/outs.json").exists()
    assert pathlib.Path("experiments/Test03/outs.json").exists()
