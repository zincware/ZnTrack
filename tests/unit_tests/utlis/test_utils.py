"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Test class for testing utils
"""
import json
import os
import pathlib
import sys
from unittest.mock import MagicMock, patch

import znjson

from zntrack.utils.utils import cwd_temp_dir, decode_dict, module_handler


def test_cwd_temp_dir():
    new_dir = cwd_temp_dir(required_files=[__file__])
    assert pathlib.Path(new_dir.name) == pathlib.Path(os.getcwd())
    assert next(pathlib.Path(new_dir.name).glob("*.py")).name == "test_utils.py"
    os.chdir("..")
    new_dir.cleanup()


def test_decode_dict_path():
    path = pathlib.Path("test.txt")
    dict_string = json.dumps(path, cls=znjson.ZnEncoder)
    loaded_dict = json.loads(dict_string)
    assert loaded_dict == {"_type": "pathlib.Path", "value": "test.txt"}
    assert decode_dict(loaded_dict) == path
    assert decode_dict(None) is None


def test_module_handler():
    my_mock = MagicMock
    my_mock.__module__ = "custom_module"
    assert module_handler(my_mock) == "custom_module"

    my_mock.__module__ = "__main__"
    with patch.object(sys, "argv", ["ipykernel_launcher"]):
        assert module_handler(my_mock) == "__main__"

    with patch.object(sys, "argv", ["pytest-runner"]):
        assert module_handler(my_mock) == "pytest-runner"
