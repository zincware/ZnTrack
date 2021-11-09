"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Test that a single stage with multiple different names works
"""
import pytest
from zntrack import Node, ZnTrackProject, dvc
import shutil
import os


@Node()
class HelloWorld:
    """BasicTest class"""

    output = dvc.result()
    inputs = dvc.params()

    def __call__(self, inputs):
        self.inputs = inputs

    def run(self):
        """Run method of the Node test instance"""
        self.output = self.inputs


def test_basic_io_assertion(tmp_path):
    """Make a simple input/output assertion test for the nodes with different names"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    project = ZnTrackProject()
    project.create_dvc_repository()

    HelloWorld()(inputs=3)
    HelloWorld(name="Test01")(inputs=17)
    HelloWorld(name="Test02")(inputs=42)

    project.repro()

    assert HelloWorld(load=True).output == 3
    assert HelloWorld(load=True, name="Test01").output == 17
    assert HelloWorld(load=True, name="Test02").output == 42
