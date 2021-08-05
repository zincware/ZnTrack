"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Add some simple integration tests
"""
import shutil

import pytest
import os
from tempfile import TemporaryDirectory

from pytrack import PyTrack, parameter, result, DVCParams, PyTrackProject

temp_dir = TemporaryDirectory()

cwd = os.getcwd()


@PyTrack()
class StageIO:
    def __init__(self):
        """Class constructor

        Definition of parameters and results
        """
        self.dvc = DVCParams(outs=['calculation.txt'])

    def __call__(self, file):
        """User input
        """

        self.dvc.deps.append(file)

    def run(self):
        """Actual computation
        """

        with open(self.dvc.deps[0], "r") as f:
            file_content = f.readlines()

        self.dvc.outs[0].write_text("".join(file_content))


@PyTrack
class StageAddition:
    def __init__(self):
        """Class constructor

        Definition of parameters and results
        """
        self.dvc = DVCParams(outs=['calculation.txt'])

        self.n_1 = parameter(int)  # seems optional now
        self.n_2 = parameter()

        self.sum = result()
        self.dif = result()

    def __call__(self, n_1, n_2):
        """User input

        Parameters
        ----------
        n_1: First number
        n_2: Second number
        """
        self.n_1 = n_1
        self.n_2 = n_2

    def run(self):
        """Actual computation"""
        self.sum = self.n_1 + self.n_2
        self.dif = self.n_1 - self.n_2

        self.dvc.outs[0].write_text(f"{self.n_1} + {self.n_2} = {self.sum}")


@PyTrack()
class StageAddition2:
    def __init__(self):
        """Class constructor

        Definition of parameters and results
        """
        self.dvc = DVCParams(outs=['calculation.txt'])

        self.n_1 = parameter(int)  # seems optional now
        self.n_2 = parameter()

        self.sum = result()
        self.dif = result()

    def __call__(self, n_1, n_2):
        """User input

        Parameters
        ----------
        n_1: First number
        n_2: Second number
        """
        self.n_1 = n_1
        self.n_2 = n_2

    def run(self):
        """Actual computation"""
        self.sum = self.n_1 + self.n_2
        self.dif = self.n_1 - self.n_2

        self.dvc.outs[0].write_text(f"{self.n_1} + {self.n_2} = {self.sum}")


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

    stage = StageAddition()
    stage(5, 10)
    project.name = "Test1"
    project.queue()

    stage = StageAddition()
    stage(50, 100)
    project.name = "Test2"
    project.run()

    project.load("Test1")
    finished_stage = StageAddition(id_=0)
    assert finished_stage.sum == 15

    project.load("Test2")
    finished_stage = StageAddition(id_=0)
    assert finished_stage.sum == 150


def test_stage_addition2():
    """Check that the dvc repro works"""
    project = PyTrackProject()
    project.create_dvc_repository()

    stage = StageAddition2()
    stage(5, 10)
    project.name = "Test1"
    project.queue()

    stage = StageAddition2()
    stage(50, 100)
    project.name = "Test2"
    project.run()

    project.load("Test1")
    finished_stage = StageAddition2(id_=0)
    assert finished_stage.sum == 15

    project.load("Test2")
    finished_stage = StageAddition2(id_=0)
    assert finished_stage.sum == 150


def test_stage_io():
    project = PyTrackProject()
    project.create_dvc_repository()

    stage = StageIO()
    stage("test_example01.py")
    project.name = "Test1"
    project.run()
    project.load()

    assert stage.dvc.outs[0].read_text().startswith('\"\"\"')
