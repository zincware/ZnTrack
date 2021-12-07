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
from time import sleep

import numpy as np

from zntrack import Node, ZnTrackProject
from zntrack.metadata import TimeIt


@Node()
class SleepNode:
    @TimeIt
    def run(self):
        self.sleep_2()
        self.sleep_5()

    @TimeIt
    def sleep_5(self):
        sleep(5)

    @TimeIt
    def sleep_2(self):
        sleep(2)


@Node()
class SleepNodeMulti:
    def run(self):
        self.sleep(1)
        self.sleep(2)
        self.sleep(3)

    @TimeIt
    def sleep(self, time):
        sleep(time)


def test_timeit(tmp_path):
    """Test that the timeit decorator works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    SleepNode()()

    project.repro()

    metadata = SleepNode(load=True).metadata

    assert len(metadata) == 3

    np.testing.assert_almost_equal(metadata["sleep_2:timeit"], 2.0, decimal=1)
    np.testing.assert_almost_equal(metadata["sleep_5:timeit"], 5.0, decimal=1)
    np.testing.assert_almost_equal(metadata["run:timeit"], 7.0, decimal=1)


def test_timeit_multi(tmp_path):
    """Test that the timeit decorator works multiple times on the same method"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    SleepNodeMulti()()

    project.repro()

    metadata = SleepNodeMulti(load=True).metadata

    assert len(metadata) == 3

    np.testing.assert_almost_equal(metadata["sleep:timeit"], 1.0, decimal=1)
    np.testing.assert_almost_equal(metadata["sleep_1:timeit"], 2.0, decimal=1)
    np.testing.assert_almost_equal(metadata["sleep_2:timeit"], 3.0, decimal=1)
