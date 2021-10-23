"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
import pytest
from zntrack import Node, ZnTrackProject, dvc
import shutil
import os


@Node()
class HelloWorld:
    """BasicTest class"""

    output = dvc.result()

    def run(self):
        """Run method of the Node test instance"""
        self.output = 43


def test_project(tmp_path):
    """Test that an ValueError is raised

    Check that a value error occurs, when accessing a result that has not been
    computed yet.

    """
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    project = ZnTrackProject()
    project.create_dvc_repository()

    HelloWorld()

    with pytest.raises(ValueError):
        _ = HelloWorld(load=True).output
