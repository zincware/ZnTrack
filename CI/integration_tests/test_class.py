from unittest import TestCase
from pytrack import PyTrack, DVC, PyTrackProject
from pathlib import Path
import json
import subprocess
import os
import shutil
from tempfile import TemporaryDirectory
import pytest

temp_dir = TemporaryDirectory()
cwd = os.getcwd()


@PyTrack()
class BasicTest:
    """BasicTest class"""

    def __init__(self):
        """Constructor of the PyTrack test instance"""
        self.deps = DVC.deps([Path("deps1", "input.json"), Path("deps2", "input.json")])
        self.parameters = DVC.params()
        self.results = DVC.result()

    def __call__(self, **kwargs):
        """Call Method of the PyTrack test instance"""
        self.parameters = kwargs

    def run(self):
        """Run method of the PyTrack test instance"""
        self.results = {"name": self.parameters["name"]}


@pytest.fixture(autouse=True)
def prepare_env():
    temp_dir = TemporaryDirectory()
    shutil.copy(__file__, temp_dir.name)
    os.chdir(temp_dir.name)

    project = PyTrackProject()
    project.create_dvc_repository()

    base = BasicTest()
    base(name="PyTest", values=[2, 4, 8, 16, 32, 64, 128, 256])

    for idx, dep in enumerate(base.deps):
        Path(dep).parent.mkdir(exist_ok=True, parents=True)
        with open(dep, "w") as f:
            json.dump({"id": idx}, f)

    project.name = "Test1"
    project.run()
    project.load()

    yield

    os.chdir(cwd)
    temp_dir.cleanup()


def test_query_by_id():
    base = BasicTest(id_=0)
    assert base.pytrack.id == "0"


def test_parameters():
    """Test that the parameters are read correctly"""
    base = BasicTest(id_=0)
    assert base.parameters == dict(name="PyTest", values=[2, 4, 8, 16, 32, 64, 128, 256])


def test_results():
    """Test that the results are read correctly"""
    base = BasicTest(id_=0)
    assert base.results == {"name": "PyTest"}


def test_deps():
    """Test that the dependencies are stored correctly"""
    base = BasicTest(id_=0)
    assert base.deps == [Path("deps1", "input.json"), Path("deps2", "input.json")]
