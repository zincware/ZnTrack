"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Simple test for #65 not interacting instances
"""
import shutil
import pytest
import os
from tempfile import TemporaryDirectory

from zntrack import Node, DVC, PyTrackProject
import numpy as np

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
        self.out = np.power(2, self.inp).item()


@pytest.fixture(autouse=True)
def prepare_env():
    """Create temporary directory"""
    temp_dir = TemporaryDirectory()
    shutil.copy(__file__, temp_dir.name)
    os.chdir(temp_dir.name)

    yield

    os.chdir(cwd)
    temp_dir.cleanup()


def test_instance_interference(tmp_path):
    """Check that the instances do not interact with each other"""
    project = PyTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    _ = ComputeA(id_=0)
    a(3)

    project.run()
    project.load()
