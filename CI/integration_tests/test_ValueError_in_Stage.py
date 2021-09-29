"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: 
"""
import pytest
from pytrack import PyTrack, PyTrackProject
import shutil
import os
from subprocess import CalledProcessError


@PyTrack()
class RaiseValueError:
    """BasicTest class"""

    def run(self):
        """Run method of the PyTrack test instance"""
        raise ValueError("Testing ValueError")


def test_project(tmp_path):
    """Test that an ValueError is raised

    Currently it is not checked, which Error occurs in the subprocess but just that the subprocess call fails.
    It only works within `project.repro` and not with `project.run`

    """
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    project = PyTrackProject()
    project.create_dvc_repository()

    error_stage = RaiseValueError()
    error_stage()

    with pytest.raises(CalledProcessError):
        project.repro()

    # with pytest.raises(CalledProcessError):
    #     project.run()

    with pytest.raises(ValueError):
        error_stage.run()
