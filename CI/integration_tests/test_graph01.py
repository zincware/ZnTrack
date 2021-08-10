"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Simple test for graph execution
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
class ComputeA:
    def __init__(self):
        self.inp = DVC.params()
        self.out = DVC.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp).item()


@PyTrack()
class ComputeB:
    def __init__(self):
        self.inp = DVC.params()
        self.out = DVC.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(3, self.inp).item()


@PyTrack()
class ComputeAB:
    def __init__(self):
        self.a = DVC.deps(ComputeA(id_=0)._pytrack_dvc.json_file.as_posix())
        self.b = DVC.deps(ComputeB(id_=0)._pytrack_dvc.json_file.as_posix())
        self.out = DVC.result()

        self.param = DVC.params()

    def __call__(self):
        self.param = "default"

    def run(self):
        a = ComputeA(id_=0).out
        b = ComputeB(id_=0).out
        self.out = a + b


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
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeAB()
    ab()

    project.run()
    subprocess.check_call(['dvc', "repro"])
    # project.load()
    finished_stage = ComputeAB(id_=0)
    assert finished_stage.out == 31
