import os
import typing as t

import pytest

# from zntrack import Node, zn
import zntrack


class CheckType(zntrack.Node):
    params: t.Any = zntrack.params()

    def run(self):
        pass


@pytest.fixture
def arg(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def fix_list() -> list:
    return list(range(10))


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

    node = CheckType(params=arg)
    assert node.params == arg
