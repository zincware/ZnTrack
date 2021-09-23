"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Test class for testing utils
"""
from pytrack.utils.utils import is_jsonable


def test_is_jsonable():
    """Test for is_jsonable

    Test is performed for a serializable dictionary and a non-serializable function.
    """
    assert is_jsonable({"a": 1}) is True
    assert is_jsonable({"a": is_jsonable}) is False
