"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""

from zntrack import Node, ZnTrackProject, zn, dvc
from zntrack.metadata import TimeIt
import os
import shutil
import numpy as np


@Node()
class HelloWorld:
    name = zn.outs()

    @TimeIt
    def run(self):
        self.name = "My Name is unknown"


@Node()
class PrintName:
    """Node that depends on HelloWorld but not on the TimeIt"""
    hello_world: HelloWorld = dvc.deps(HelloWorld(load=True))

    def run(self):
        print(self.hello_world.name)


def test_metadata_dependency(tmp_path):
    """Test that dependencies are correct"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    hello_world = HelloWorld()
    print_name = PrintName()

    hello_world()
    print_name()

    project.repro()

    # should only depend on the dvc.outs and not on the metric
    assert len(set(PrintName(load=True).zntrack.dvc.deps)) == 1


def test_metadata_dependency_calling_multiple_times(tmp_path):
    """Test that dependencies are correct even when calling multiple times"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    hello_world = HelloWorld()
    print_name = PrintName()

    # Try calling it twice for testing this too
    hello_world()
    hello_world()
    hello_world()
    print_name()
    print_name()
    print_name()

    project.repro()

    assert len(set(PrintName(load=True).zntrack.dvc.deps)) == 1
