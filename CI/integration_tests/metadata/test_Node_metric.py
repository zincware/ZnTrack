"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""

from zntrack import Node, ZnTrackProject
from zntrack.metadata import TimeIt
from time import sleep
import os
import shutil
import numpy as np


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


def test_timeit(tmp_path):
    """Test that the timeit decorator works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    SleepNode()()

    project.repro()

    metadata = SleepNode(load=True).metadata

    np.testing.assert_almost_equal(metadata['sleep_2:timeit'], 2., decimal=1)
    np.testing.assert_almost_equal(metadata['sleep_5:timeit'], 5., decimal=1)
    np.testing.assert_almost_equal(metadata['run:timeit'], 7., decimal=1)

