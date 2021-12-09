"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: 
"""
from unittest.mock import Mock
from zntrack.metadata.decorators import TimeIt


def cls_method(self):
    """Any cls method that will be timed"""
    pass


def test_timeit():
    """Assume that metadata is empty and this is the first run"""
    time_it = TimeIt(cls_method)
    cls_mock = Mock()
    cls_mock.metadata = {}
    time_it(cls_mock)

    assert cls_mock.metadata.keys() == {"cls_method:timeit": 0.0}.keys()
    assert all([isinstance(x, float) for x in cls_mock.metadata.values()])


def test_timeit_multi_run():
    """Run timeit multiple times and append the metadata"""
    time_it = TimeIt(cls_method)
    cls_mock = Mock()
    cls_mock.metadata = {}
    time_it(cls_mock)
    time_it(cls_mock)

    assert (
        cls_mock.metadata.keys()
        == {"cls_method:timeit": 0.0, "cls_method_1:timeit": 0.0}.keys()
    )
    assert all([isinstance(x, float) for x in cls_mock.metadata.values()])
