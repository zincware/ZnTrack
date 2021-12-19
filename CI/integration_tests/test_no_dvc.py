"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: 
"""
import os
import subprocess

import pytest

from zntrack import Node, dvc


@Node()
class HelloWorld:
    param = dvc.params(42)

    def __call__(self, *args, **kwargs):
        pass

    def run(self):
        pass


def test_no_dvc_true(tmp_path):
    os.chdir(tmp_path)
    HelloWorld()(no_dvc=True)
    assert HelloWorld(load=True).param == 42


def test_no_dvc_false(tmp_path):
    """Default behaviour when not inside a DVC repository"""
    os.chdir(tmp_path)
    with pytest.raises(subprocess.CalledProcessError):
        HelloWorld()(no_dvc=False)
