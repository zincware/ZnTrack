"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
import os

import pytest

from zntrack import Node, dvc


@Node()
class CheckType:
    params = dvc.params()

    def __call__(self, params):
        self.params = params

    def run(self):
        pass


@pytest.fixture
def arg(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def fix_list() -> list:
    return [x for x in range(10)]


@pytest.fixture
def fix_dict() -> dict:
    # keys must be of type str!
    return {str(key): val for key, val in enumerate(range(10))}


@pytest.fixture
def fix_int() -> int:
    return 42


@pytest.fixture
def fix_empty_list() -> list:
    return []


@pytest.mark.parametrize(
    "arg", ["fix_list", "fix_int", "fix_dict", "fix_empty_list"], indirect=True
)
def test_params(arg, tmp_path):
    os.chdir(tmp_path)

    CheckType()(params=arg)

    assert CheckType(load=True).params == arg
