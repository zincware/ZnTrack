from unittest import TestCase
from pytrack import PyTrack
from typing import Union
import subprocess
import shutil

import os
from tempfile import TemporaryDirectory

temp_dir = TemporaryDirectory()


class BasicTest(PyTrack):
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
        self.json_file = False
        self.post_init(id_, filter_)

    def __call__(self):
        """Call Method of the PyTrack test instance"""
        self.post_call()

    def run(self):
        """Run method of the PyTrack test instance"""
        self.pre_run()


class TestBasic(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        """Prepare for tests

        1. copy file to temp_dir
        2. chdir into temp_dir
        3. Initalize DVC

        """
        shutil.copy(__file__, temp_dir.name)
        os.chdir(temp_dir.name)

        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['dvc', 'init'])

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove all test files"""
        subprocess.check_call(['dvc', 'destroy', "-f"])
        os.chdir('..')
        temp_dir.cleanup()

    def test_building_class(self):
        """Run an integration test"""
        base = BasicTest()
        # Have to run dvc repro here, because otherwise I can not test the values inside it
        base()
        subprocess.check_call(['dvc', 'repro'])
