"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
from pytrack import PyTrack, DVC, PyTrackProject
import os


@PyTrack()
class HelloWorld:
    def __init__(self):
        self.argument_1 = DVC.params()

    def __call__(self, argument_1):
        self.argument_1 = argument_1

    def run(self):
        pass


@PyTrack()
class HelloWorldwDefault:
    def __init__(self):
        self.argument_1 = DVC.params(314159)

    def __call__(self, argument_1):
        self.argument_1 = argument_1

    def run(self):
        pass


def test_init_without_overwriting(tmp_path):
    """Test that initializing empty DVC.params does not result in changing values"""
    os.chdir(tmp_path)
    project = PyTrackProject()
    project.create_dvc_repository()

    hello_world_1 = HelloWorld()
    hello_world_1(argument_1=11235)

    hello_world_2 = HelloWorld()

    # it should not overwrite the given param values,
    #  when they are not set explicitly!

    assert hello_world_1.argument_1 == 11235


def test_load_works(tmp_path):
    """Test that pre-initializing DVC.params does result in changing values"""
    os.chdir(tmp_path)
    project = PyTrackProject()
    project.create_dvc_repository()

    hello_world_1 = HelloWorldwDefault()
    hello_world_1(argument_1=11235)

    assert HelloWorldwDefault().argument_1 == 314159
    assert HelloWorldwDefault(load=True).argument_1 == 11235
