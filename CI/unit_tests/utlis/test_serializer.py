"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: tests for the serializers and deserializers
"""

from zntrack.utils.serializer import serializer, deserializer
import pytest
from pathlib import Path
import numpy as np


@pytest.fixture
def path_dict():
    return {
        "a": {"b": {"c": Path("hello1.py"), "d": "hello2.py"}, "e": Path("hello3.py"),}
    }


@pytest.fixture
def np_dict():
    return {
        "a": {
            "b": {"c": np.arange(1, 5), "d": np.arange(5, 10)},
            "e": np.arange(10, 15),
        }
    }


def test_serializer_path_dict(path_dict):
    """Test that serializing Path works"""
    assert serializer(path_dict) == {
        "a": {
            "b": {"c": {"Path": "hello1.py"}, "d": "hello2.py"},
            "e": {"Path": "hello3.py"},
        }
    }


def test_unserialize_path_dict(path_dict):
    """Test that deserializing Path works"""
    serialized_path_dict = serializer(path_dict)
    deserialized_path_dict = deserializer(serialized_path_dict)

    assert deserialized_path_dict == path_dict


def test_serializer_numpy_dict(np_dict):
    """Test that serializing numpy works"""
    assert serializer(np_dict) == {
        "a": {
            "b": {"c": {"np": [1, 2, 3, 4]}, "d": {"np": [5, 6, 7, 8, 9]}},
            "e": {"np": [10, 11, 12, 13, 14]},
        }
    }


def test_unserialize_numpy_dict(np_dict):
    """Test that unserializing numpy works"""
    serialized_np_dict = serializer(np_dict)
    deserialized_np_dict = deserializer(serialized_np_dict)
    np.testing.assert_array_equal(
        deserialized_np_dict["a"]["b"]["c"], np_dict["a"]["b"]["c"]
    )
    np.testing.assert_array_equal(
        deserialized_np_dict["a"]["b"]["d"], np_dict["a"]["b"]["d"]
    )
    np.testing.assert_array_equal(deserialized_np_dict["a"]["e"], np_dict["a"]["e"])
