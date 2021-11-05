"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: 
"""
import pytest
from zntrack import Node
import os


@Node()
class HelloWorld:
    def run(self):
        pass


def test_pre_call(tmp_path):
    """Check, that calling a loaded Node raises an error"""
    os.chdir(tmp_path)

    hello_world = HelloWorld(load=True)

    with pytest.raises(ValueError):
        hello_world()
