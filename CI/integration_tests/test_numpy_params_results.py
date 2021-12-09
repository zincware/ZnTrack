"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Test for serialized numpy
"""

import os
import shutil
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from zntrack import Node, ZnTrackProject, dvc

temp_dir = TemporaryDirectory()

cwd = os.getcwd()


@Node()
class ComputeA:
    """Node stage A"""

    def __init__(self):
        self.inp = dvc.params()
        self.out = dvc.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp)


def test_stage_addition(tmp_path):
    """Check that the dvc repro works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(np.arange(5))

    project.run()
    project.repro()
    finished_stage = ComputeA(id_=0)
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))


def test_stage_addition_run(tmp_path):
    """Check that the PyTracks run method works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(np.arange(5))

    a.run()

    finished_stage = ComputeA(id_=0)
    np.testing.assert_array_equal(finished_stage.out, np.array([1, 2, 4, 8, 16]))
    np.testing.assert_array_equal(finished_stage.inp, np.arange(5))
