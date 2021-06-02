import time
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

    def __init__(self):
        super().__init__()
        self.dvc = DVCParams(
            params_file="params.json",
            deps=[Path('outs', 'input.json')]
        )

    def __call__(self, name):
        self.parameters = {"name": name}
        self.post_call()

    def run_dvc(self, id_=0):
        self.pre_run(id_)
        self.results = {'name': self.parameters['name']}


class TestBasic(TestCase):

    @classmethod
    def setUpClass(cls) -> None:

        tmp_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy(__file__, tmp_dir)
        os.chdir(tmp_dir)

        subprocess.check_call(['git', 'init'])
        subprocess.check_call(['dvc', 'init'])

        base = BasicTest()
        deps = base.dvc.deps[0]
        deps.parent.mkdir(exist_ok=True, parents=True)

        with open(deps, "w") as f:
            json.dump(dict(name="Hello World"), f)

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove all test files"""
        subprocess.check_call(['dvc', 'destroy', "-f"])
        os.chdir('..')
        shutil.rmtree(tmp_dir)

    def test_basic(self):
        base = BasicTest()
        base(name='MyTest')

        subprocess.check_call(['dvc', 'repro'])

        with open(base.files.json_file) as f:
            file_read = json.load(f)

        self.assertTrue(file_read == dict(name="MyTest"))


if __name__ == '__main__':
    base = BasicTest()
    base(name='MyTest')

    base.run_dvc()
