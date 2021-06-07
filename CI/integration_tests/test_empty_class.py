from unittest import TestCase
from pytrack import PyTrack
from pathlib import Path
from typing import Union

import subprocess
import shutil

import os

tmp_dir = Path('tmp_dir')


class BasicTest(PyTrack):
    def __init__(self, id_: Union[int, str] = None, filter_: dict = None):
        super().__init__()
        self.json_file = False
        self.post_init(id_, filter_)

    def __call__(self):
        self.post_call()

    def run_dvc(self):
        self.pre_run()


class TestBasic(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        tmp_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy(__file__, tmp_dir)
        os.chdir(tmp_dir)

        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['dvc', 'init'])

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove all test files"""
        subprocess.check_call(['dvc', 'destroy', "-f"])
        os.chdir('../../tests')
        shutil.rmtree(tmp_dir)

    def test_building_class(self):
        base = BasicTest()
        # Have to run dvc repro here, because otherwise I can not test the values inside it
        base()
        subprocess.check_call(['dvc', 'repro'])
