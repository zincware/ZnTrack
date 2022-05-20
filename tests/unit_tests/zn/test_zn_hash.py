import pytest

from zntrack import zn


class ExampleNodeWithTime:
    hash = zn.Hash()

    def __hash__(self):
        return 1234


def test_hash():
    assert ExampleNodeWithTime().hash != ExampleNodeWithTime().hash

    with pytest.raises(ValueError):
        example = ExampleNodeWithTime()
        example.hash = 1234


class ExampleNode:
    hash = zn.Hash(use_time=False)

    def __hash__(self):
        return 1234


def test_constant_hash():
    assert ExampleNode().hash == 1234
    assert ExampleNode().hash == ExampleNode().hash
