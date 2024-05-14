"""Zntrack apply module for custom "run" methods."""

import typing as t

o = t.TypeVar("o")


def apply(obj: o, method: str) -> o:
    """Return a new object like "o" which has the method string attached."""

    class _(obj):
        _method = method

    _.__module__ = obj.__module__
    _.__name__ = obj.__name__

    return _
