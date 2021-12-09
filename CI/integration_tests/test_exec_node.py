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

from zntrack import Node, ZnTrackProject, dvc


@Node(no_exec=False)
class HelloWorld:

    output = dvc.result()

    def __call__(self, *args, **kwargs):
        pass

    def run(self):
        self.output = 43


@Node(exec_=True)
class HelloWorldDepreciated:

    output = dvc.result()

    def __call__(self, *args, **kwargs):
        pass

    def run(self):
        self.output = 43


def test_project(tmp_path):
    """Test that Nodes with no_exec=False work"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    project = ZnTrackProject()
    project.create_dvc_repository()

    HelloWorld()()

    assert HelloWorld(load=True).output == 43


def test_project_depreciated(tmp_path):
    """Test that Nodes with exec_=True work"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    project = ZnTrackProject()
    project.create_dvc_repository()

    HelloWorldDepreciated()()

    assert HelloWorldDepreciated(load=True).output == 43
