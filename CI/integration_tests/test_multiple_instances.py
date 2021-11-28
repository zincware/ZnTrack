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

from zntrack import Node, dvc, ZnTrackProject
import numpy as np

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
        self.out = np.power(2, self.inp).item()


def test_load_before_repro(tmp_path):
    """Check that the instances do not interact with each other"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    _ = ComputeA(id_=0)
    a(3)

    project.repro()
