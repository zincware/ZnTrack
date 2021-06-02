from unittest import TestCase
from dvc_op.core.dvc_op import DVCOp
from dvc_op.core.dataclasses import DVCParams
from pathlib import Path
import json

import subprocess
import shutil

import os

tmp_dir = Path('tmp_dir')


class BasicTest(DVCOp):
    def config(self):
        self.json_file = False

    def __call__(self):
        self.post_call()

    def run_dvc(self, id_=0):
        self.pre_run(id_)


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
        os.chdir('..')
        shutil.rmtree(tmp_dir)

    def test_building_class(self):
        base = BasicTest()
        # Have to run dvc repro here, because otherwise I can not test the values inside it
        base()
        subprocess.check_call(['dvc', 'repro'])
