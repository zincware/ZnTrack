from unittest import TestCase
from PyTrack import DVCOp, DVCParams
from pathlib import Path
import json

import subprocess
import shutil

import os

tmp_dir = Path('tmp_dir')


class BasicTest(DVCOp):

    def config(self):
        self.dvc = DVCParams(
            params_file="params.json",
            deps=[Path('deps1', 'input.json'), Path('deps2', 'input.json')]
        )

    def __call__(self, **kwargs):
        self.parameters = kwargs
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
        for idx, dep in enumerate(base.dvc.deps):
            dep.parent.mkdir(exist_ok=True, parents=True)
            with open(dep, "w") as f:
                json.dump({'id': idx}, f)

        # Have to run dvc repro here, because otherwise I can not test the values inside it
        base(name="PyTest", values=[2, 4, 8, 16, 32, 64, 128, 256])
        subprocess.check_call(['dvc', 'repro'])

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove all test files"""
        subprocess.check_call(['dvc', 'destroy', "-f"])
        os.chdir('..')
        shutil.rmtree(tmp_dir)

    def test_query_by_id(self):
        base = BasicTest(id_=0)
        self.assertTrue(base.id, "0")

    def test_query_by_name(self):
        base = BasicTest(filter_={'name': 'PyTest'})
        self.assertTrue(base.id, "0")

    def test_query_obj_id(self):
        base = BasicTest()
        out = base.query_obj(0)
        self.assertTrue(out.id, "0")

    def test_query_obj_name(self):
        base = BasicTest()
        out = base.query_obj(dict(name="PyTest"))
        self.assertTrue(len(out), 1)
        self.assertTrue(out[0].id, "0")

    def test_parameters(self):
        base = BasicTest(id_=0)
        self.assertTrue(base.parameters, dict(name="PyTest", values=[2, 4, 8, 16, 32, 64, 128, 256]))

    def test_results(self):
        base = BasicTest(id_=0)
        self.assertTrue(base.results, {'name': 'PyTest'})

    def test_deps(self):
        base = BasicTest(id_=0)
        self.assertTrue(base.files.deps, [Path('deps1', 'input.json'), Path('deps2', 'input.json')])

    def test_params_file(self):
        base = BasicTest(id_=0)
        self.assertTrue(base.dvc.params_file, "params.json")
