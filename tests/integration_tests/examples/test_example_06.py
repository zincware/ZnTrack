import os

import pytest

from zntrack import Node, zn


class CheckType(Node):
    params = zn.params()

    def __init__(self, params=None, **kwargs):
        super().__init__(**kwargs)
        self.params = params

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


# @pytest.fixture
# def fix_empty_list() -> list:
#     return []


@pytest.mark.parametrize("arg", ["fix_list", "fix_int", "fix_dict"], indirect=True)
def test_params(arg, tmp_path):
    os.chdir(tmp_path)

    CheckType(params=arg).save()

    assert CheckType.load().params == arg
