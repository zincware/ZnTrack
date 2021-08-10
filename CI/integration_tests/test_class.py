from unittest import TestCase
from pytrack import PyTrack, DVC
from pathlib import Path
import json
import subprocess
import os
import shutil
from tempfile import TemporaryDirectory

temp_dir = TemporaryDirectory()


@PyTrack()
class BasicTest:
    """BasicTest class"""

    def __init__(self):
        """Constructor of the PyTrack test instance"""
        self.deps1 = DVC.deps(Path("deps1", "input.json").as_posix())
        self.deps2 = DVC.deps(Path("deps2", "input.json").as_posix())
        self.parameters = DVC.params()
        self.results = DVC.result()

    def __call__(self, **kwargs):
        """Call Method of the PyTrack test instance"""
        self.parameters = kwargs

    def run(self):
        """Run method of the PyTrack test instance"""
        self.results = {"name": self.parameters["name"]}


class TestBasic(TestCase):
    """This is a unittest TestCase for testing PyTrack"""

    @classmethod
    def setUpClass(cls) -> None:
        """Prepare for tests

        1. copy file to temp_dir
        2. chdir into temp_dir
        3. Initalize DVC
        4. run dvc repro

        """
        shutil.copy(__file__, temp_dir.name)
        os.chdir(temp_dir.name)

        subprocess.check_call(["git", "init"])
        subprocess.check_call(["dvc", "init"])

        base = BasicTest()

        for idx, dep in enumerate([base.deps1, base.deps2]):
            Path(dep).parent.mkdir(exist_ok=True, parents=True)
            with open(dep, "w") as f:
                json.dump({"id": idx}, f)

        # Have to run dvc repro here, because otherwise I can not test the values inside it
        base(name="PyTest", values=[2, 4, 8, 16, 32, 64, 128, 256])
        subprocess.check_call(["dvc", "repro"])

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove all test files"""
        subprocess.check_call(["dvc", "destroy", "-f"])
        os.chdir("..")
        temp_dir.cleanup()

    def test_query_by_id(self):
        """Test that the id is set correctly"""
        base = BasicTest(id_=0)
        self.assertTrue(base._pytrack_id, "0")

    def test_parameters(self):
        """Test that the parameters are read correctly"""
        base = BasicTest(id_=0)
        self.assertTrue(
            base.parameters, dict(name="PyTest", values=[2, 4, 8, 16, 32, 64, 128, 256])
        )

    def test_results(self):
        """Test that the results are read correctly"""
        base = BasicTest(id_=0)
        self.assertTrue(base.results, {"name": "PyTest"})

    def test_deps(self):
        """Test that the dependencies are stored correctly"""
        base = BasicTest(id_=0)
        self.assertTrue(
            base.deps1, Path("deps1", "input.json")
        )
        self.assertTrue(
            base.deps2, Path("deps2", "input.json")
        )
