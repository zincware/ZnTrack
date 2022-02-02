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

import pytest
import znjson

from zntrack.utils import utils


def test_is_jsonable():
    """Test for is_jsonable

    Test is performed for a serializable dictionary and a non-serializable function.
    """
    assert utils.is_jsonable({"a": 1}) is True
    assert utils.is_jsonable({"a": utils.is_jsonable}) is False


def test_cwd_temp_dir():
    new_dir = utils.cwd_temp_dir(required_files=[__file__])
    assert pathlib.Path(new_dir.name) == pathlib.Path(os.getcwd())
    assert next(pathlib.Path(new_dir.name).glob("*.py")).name == "test_utils.py"
    os.chdir("..")
    new_dir.cleanup()


def test_decode_dict_path():
    path = pathlib.Path("test.txt")
    dict_string = json.dumps(path, cls=znjson.ZnEncoder)
    loaded_dict = json.loads(dict_string)
    assert loaded_dict == {"_type": "pathlib.Path", "value": "test.txt"}
    assert utils.decode_dict(loaded_dict) == path
    assert utils.decode_dict(None) is None


class Test:
    pass


def test_get_auto_init():
    with pytest.raises(TypeError):
        Test(foo="foo")

    setattr(Test, "__init__", utils.get_auto_init(fields=["foo", "bar"]))

    test = Test(foo="foo", bar="bar")

    assert test.foo == "foo"
    assert test.bar == "bar"


def test_module_handler():
    my_mock = MagicMock
    my_mock.__module__ = "custom_module"
    assert utils.module_handler(my_mock) == "custom_module"

    my_mock.__module__ = "__main__"
    with patch.object(sys, "argv", ["ipykernel_launcher"]):
        assert utils.module_handler(my_mock) == "__main__"

    with patch.object(sys, "argv", ["pytest-runner"]):
        assert utils.module_handler(my_mock) == "pytest-runner"
