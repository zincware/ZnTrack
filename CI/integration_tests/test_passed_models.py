"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Another test for PyTest
"""
import shutil
import subprocess

import pytest
import os
from tempfile import TemporaryDirectory

from pytrack import PyTrack, DVC, PyTrackProject
import numpy as np

temp_dir = TemporaryDirectory()

cwd = os.getcwd()


# TODO tests should also test .run() and not just dvc repro for better coverage!

@PyTrack()
class Model:
    def __init__(self):
        self.model_params = DVC.params()
        self.model_class = DVC.params()

        self.model_dict = {
            TestModel1.__name__: TestModel1,
            TestModel2.__name__: TestModel2
        }

        self.result = DVC.result()

    def __call__(self, model):
        self.model_params = model.params
        self.model_class = model.__class__.__name__

    def run(self):
        model = self.model_dict[self.model_class](parent=self, **self.model_params)
        model.run()


class TestModel1:
    def __init__(self, param1, parent=None):
        self.params = {"param1": param1}
        self.parent: Model = parent

    def run(self):
        self.parent.result = f"TestModel1 received params: {self.params}!"


class TestModel2:
    def __init__(self, param1, param2, parent=None):
        self.params = {"param1": param1, "param2": param2}
        self.parent: Model = parent

    def run(self):
        self.parent.result = f"TestModel2 received params: {self.params}!"


@pytest.fixture(autouse=True)
def prepare_env():
    temp_dir = TemporaryDirectory()
    shutil.copy(__file__, temp_dir.name)
    os.chdir(temp_dir.name)

    yield

    os.chdir(cwd)
    temp_dir.cleanup()


def test_stage_addition():
    """Check that the dvc repro works"""
    project = PyTrackProject()
    project.create_dvc_repository()

    test_model_1 = TestModel1(15)
    test_model_2 = TestModel2(10, 5)

    model = Model()
    model(model=test_model_1)

    project.name = "TestModel1"
    project.queue()

    model = Model()
    model(model=test_model_2)

    project.name = "TestModel2"
    project.run()

    project.load("TestModel1")
    model = Model(id_=0)
    assert model.result == "TestModel1 received params: {'param1': 15}!"

    project.load("TestModel2")
    model = Model(id_=0)
    assert model.result == "TestModel2 received params: {'param1': 10, 'param2': 5}!"
