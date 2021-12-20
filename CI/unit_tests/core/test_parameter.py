"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: 
"""

from unittest.mock import Mock

import pytest

from zntrack.core.parameter import ZnTrackOption


def test__get_default():
    class MyNode:
        test_option = ZnTrackOption(default_value="Lorem Ipsum")

    my_node = MyNode()

    assert my_node.test_option == "Lorem Ipsum"


def test__get_no_default():
    class MyNode:
        test_option = ZnTrackOption()
        zntrack = Mock()

    my_node = MyNode()
    my_node.zntrack.load = True

    # Raise Error when loaded
    with pytest.raises(ValueError):
        _ = my_node.test_option

    my_node = MyNode()
    my_node.zntrack.load = False

    # also raise a ValueError - but this is a very unlikely scenario and raises a
    # different error message
    with pytest.raises(ValueError):
        _ = my_node.test_option


def test__set_non_load():
    class MyNode:
        test_option = ZnTrackOption()
        zntrack = Mock()

    my_node = MyNode()

    # Non-loaded case for dvc.<option>
    my_node.zntrack.load = False
    my_node.test_option = "Lorem Ipsum"
    assert my_node.test_option == "Lorem Ipsum"

    # Loaded case for dvc.<option>
    my_node.zntrack.load = True
    with pytest.raises(ValueError):
        my_node.test_option = "Lorem Ipsum"


def test__set_load():
    class MyNode:
        test_option = ZnTrackOption(load=True)
        zntrack = Mock()

    my_node = MyNode()

    # Non-loaded case for zn.<option>
    my_node.zntrack.load = True
    my_node.zntrack.running = True
    my_node.test_option = "Lorem Ipsum"
    assert my_node.test_option == "Lorem Ipsum"

    # Loaded case for zn.<option>
    my_node.zntrack.load = True
    my_node.zntrack.running = False
    with pytest.raises(ValueError):
        my_node.test_option = "Lorem Ipsum"


def test_custom_get():
    class CustomOption(ZnTrackOption):
        def _get(self, instance, owner):
            return "Lorem Ipsum"

    class MyNode:
        test_option = CustomOption()

    assert MyNode().test_option == "Lorem Ipsum"


def test_custom_set():
    class CustomOption(ZnTrackOption):
        def _set(self, instance, value):
            instance.__dict__["test"] = value

    class MyNode:
        test_option = CustomOption()

    my_node = MyNode()
    my_node.test_option = "Lorem Ipsum"

    assert my_node.__dict__["test"] == "Lorem Ipsum"


def test_init_w_default():
    with pytest.raises(ValueError):
        ZnTrackOption(default_value="Lorem Ipsum", load=True)


def test_access_without_init():
    class MyNode:
        test_option = ZnTrackOption(default_value="Lorem Ipsum")

    # When accessing an option without calling the __init__ it will yield the default.
    assert MyNode.test_option == "Lorem Ipsum"


def test_tuple_to_list():
    class MyNode:
        test_option = ZnTrackOption(default_value=(1, 2, 3))

    # tuples will always be converted to lists internally, because json does not
    # distinguish between lists and tuples
    my_node = MyNode()
    assert my_node.test_option == [1, 2, 3]
