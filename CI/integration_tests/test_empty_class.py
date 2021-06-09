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
        super().__init__()
        self.json_file = False
        self.post_init(id_, filter_)

    def __call__(self):
        self.post_call()

    def run(self):
        self.pre_run()


class TestBasic(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
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
        base = BasicTest()
        # Have to run dvc repro here, because otherwise I can not test the values inside it
        base()
        subprocess.check_call(['dvc', 'repro'])
