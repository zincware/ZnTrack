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

from zntrack import Node, DVC, ZnTrackProject
from pathlib import Path

temp_dir = TemporaryDirectory()

cwd = os.getcwd()


@Node()
class StageIO:
    def __init__(self):
        """Class constructor

        Definition of parameters and results
        """
        self.outs = DVC.outs(Path("calculation.txt"))
        self.deps = DVC.deps()
        self.param = DVC.params()

    def __call__(self, file):
        """User input"""
        self.param = file
        self.deps = file

    def run(self):
        """Actual computation"""

        with open(self.deps, "r") as f:
            file_content = f.readlines()

        Path(self.outs).write_text("".join(file_content))


@Node()
class StageAddition:
    def __init__(self):
        """Class constructor

        Definition of parameters and results
        """
        self.outs = DVC.outs(Path("calculation.txt"))

        self.n_1 = DVC.params()  # seems optional now
        self.n_2 = DVC.params()

        self.sum = DVC.result()
        self.dif = DVC.result()

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

        Path(self.outs).write_text(f"{self.n_1} + {self.n_2} = {self.sum}")


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
    project = ZnTrackProject()
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


def test_stage_io():
    project = ZnTrackProject()
    project.name = "Test1"
    project.create_dvc_repository()

    deps = Path("test_example_01.py")

    stage = StageIO()
    stage(deps.resolve())
    project.run()
    project.load()

    stage = StageIO(id_=0)

    assert stage.outs.read_text().startswith('"""')
