"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Test for serialized numpy
"""

import shutil

import pytest
import os
from tempfile import TemporaryDirectory

from zntrack import Node, DVC, ZnTrackProject
import numpy as np

temp_dir = TemporaryDirectory()

cwd = os.getcwd()


@Node()
class ComputeA:
    """Node stage A"""

    def __init__(self):
        self.inp = DVC.params()
        self.out = DVC.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp)


@pytest.fixture(autouse=True)
def prepare_env():
    """Create temporary directory"""
    temp_dir = TemporaryDirectory()
    shutil.copy(__file__, temp_dir.name)
    os.chdir(temp_dir.name)

    yield

    os.chdir(cwd)
    temp_dir.cleanup()


def test_stage_addition():
    """Check that the dvc repro works"""
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(np.arange(5))

    project.run()
    project.load()
    finished_stage = ComputeA(id_=0)
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))


def test_stage_addition_run():
    """Check that the PyTracks run method works"""
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(np.arange(5))

    a.run()

    finished_stage = ComputeA(id_=0)
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))
