"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Add some simple integration tests
"""
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from zntrack import Node, ZnTrackProject, dvc

temp_dir = TemporaryDirectory()

cwd = os.getcwd()


@Node()
class StageIO:
    def __init__(self):
        """Class constructor

        Definition of parameters and results
        """
        self.outs = dvc.outs(Path("calculation.txt"))
        self.deps = dvc.deps()
        self.param = dvc.params()

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
        self.outs = dvc.outs(Path("calculation.txt"))

        self.n_1 = dvc.params()  # seems optional now
        self.n_2 = dvc.params()

        self.sum = dvc.result()
        self.dif = dvc.result()

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


def test_stage_addition(tmp_path):
    """Check that the dvc repro works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
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
    project.repro()

    project.load("Test1")
    finished_stage = StageAddition(id_=0)
    assert finished_stage.sum == 15

    project.load("Test2")
    finished_stage = StageAddition(id_=0)
    assert finished_stage.sum == 150


def test_stage_io(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "Test1"
    project.create_dvc_repository()

    deps = Path("test_example_01.py")

    stage = StageIO()
    stage(deps.resolve())
    project.repro()

    stage = StageIO(id_=0)

    assert stage.outs.read_text().startswith('"""')
