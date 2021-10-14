"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
from pytrack import PyTrack, DVC
import shutil
import os


@PyTrack()
class Stage1:
    args = DVC.params()

    def __call__(self, args):
        self.args = args

    def run(self):
        pass


@PyTrack()
class Stage2:
    stage_1: Stage1 = DVC.deps(Stage1(load=True))

    def __call__(self, *args, **kwargs):
        pass

    def run(self):
        pass


def test_stage_stage_dependency(tmp_path):
    """Test that stage dependencies including load work as expected"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    stage_1 = Stage1()
    stage_1(args='Test01')
    # Need to call the stage, to create the config file
    #  it does not make sense to access the results of a stage
    #  that has not at least been called
    stage_2 = Stage2()
    stage_2()

    stage_2a = Stage2(load=True)

    # changing the value of Stage1 in the config file
    stage_1 = Stage1()
    stage_1(args='Test02')

    # Loading the stage it should now have the new value
    stage_2b = Stage2(load=True)

    assert stage_2a.stage_1.args == "Test01"
    assert stage_2b.stage_1.args == "Test02"
