import pytest

from zntrack.utils.structs import LazyOption


def test_noLazyOptionInit():
    with pytest.raises(ValueError):
        LazyOption()
