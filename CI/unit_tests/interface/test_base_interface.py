"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: 
"""
import os
import shutil

from zntrack.interface import DVCInterface
import pytest

from zntrack import Node, dvc, zn
import subprocess


@Node()
class HelloWorld:
    outputs = zn.outs()
    inputs = dvc.params()

    def __call__(self, inputs):
        self.inputs = inputs

    def run(self):
        self.outputs = self.inputs


@pytest.fixture()
def single_experiment_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.run(['git', 'init'])
    subprocess.run(['dvc', 'init'])

    HelloWorld()(inputs=1)
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', 'Init'])

    subprocess.run(['dvc', 'repro'])

    return tmp_path


def test_experiments(single_experiment_path):
    """Check that loading works and look for the default workspace environment"""
    os.chdir(single_experiment_path)

    interface = DVCInterface()
    assert "workspace" in interface.experiments
