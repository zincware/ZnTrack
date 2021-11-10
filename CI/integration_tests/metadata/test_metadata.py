"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""

from zntrack import Node, zn
from zntrack.metadata import TimeIt
import os
import shutil
import pytest


@Node()
class HelloWorld:
    metadata = zn.metrics()

    @TimeIt
    def run(self):
        pass


@Node()
class HelloWorldInit:
    def __init__(self):
        self.metadata = zn.metrics()

    @TimeIt
    def run(self):
        pass


def test_metadata_already_exists_error(tmp_path):
    """Test that it raises an error if metadata is already defined"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    with pytest.raises(AttributeError):
        HelloWorld()

    with pytest.raises(AttributeError):
        HelloWorldInit()
