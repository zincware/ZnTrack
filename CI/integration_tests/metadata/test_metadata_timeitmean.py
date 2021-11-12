"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""

from zntrack import Node, ZnTrackProject
from zntrack.metadata import TimeItMean
from time import sleep
import os
import shutil
import numpy as np


@Node()
class SleepNode:
    def run(self):
        for _ in range(10):
            self.sleep(1)

    @TimeItMean
    def sleep(self, time):
        sleep(time)


def test_timeitmean(tmp_path):
    """Test that the timeitMean decorator works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    SleepNode()()

    project.repro()

    metadata = SleepNode(load=True).metadata

    np.testing.assert_almost_equal(metadata["sleep:TimeItMean"]['mean'], 1.0, decimal=3)
    np.testing.assert_almost_equal(metadata["sleep:TimeItMean"]['std'], 0.0, decimal=3)
    assert metadata["sleep:TimeItMean"]['runs'] == 10
