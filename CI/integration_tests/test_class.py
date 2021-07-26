from unittest import TestCase
from pytrack import PyTrack, DVCParams
from pathlib import Path
import json
from typing import Union
import subprocess
import os
import shutil
from tempfile import TemporaryDirectory

temp_dir = TemporaryDirectory()


class BasicTest(PyTrack):
    """BasicTest class"""

    def __init__(self, id_: Union[int, str] = None, filter_: dict = None):
        """Constructor of the PyTrack test instance

        Parameters
        ----------
        id_: int, str, optional
            Optional primary key to query a previously created stage
        filter_: dict, optional
            Optional second method to query - only executed if id_ = None - using a dictionary with parameters key pairs
            This will always return the first instance. If multiple instances are possible use query_obj()!
        """
        super().__init__()
        self.dvc = DVCParams(
            params_file="params.json",
            deps=[Path("deps1", "input.json"), Path("deps2", "input.json")],
        )
        self.post_init(id_, filter_)

    def __call__(self, **kwargs):
        """Call Method of the PyTrack test instance"""
        self.parameters = kwargs
        self.post_call()

    def run(self):
        """Run method of the PyTrack test instance"""
        self.pre_run()
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
        for idx, dep in enumerate(base.dvc.deps):
            dep.parent.mkdir(exist_ok=True, parents=True)
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
        self.assertTrue(base.id, "0")

    def test_query_by_name(self):
        """Test that query by name works"""
        base = BasicTest(filter_={"name": "PyTest"})
        self.assertTrue(base.id, "0")

    def test_query_obj_id(self):
        """Test that query by id works"""
        base = BasicTest()
        out = base.query_obj(0)
        self.assertTrue(out.id, "0")

    def test_query_obj_name(self):
        """Test that query_obj works and returns te correct new instance"""
        base = BasicTest()
        out = base.query_obj(dict(name="PyTest"))
        self.assertTrue(len(out), 1)
        self.assertTrue(out[0].id, "0")

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
            base.files.deps, [Path("deps1", "input.json"), Path("deps2", "input.json")]
        )

    def test_params_file(self):
        """Test that the params file has to correct name"""
        base = BasicTest(id_=0)
        self.assertTrue(base.dvc.params_file, "params.json")
