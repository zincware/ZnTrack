"""Zntrack apply module for custom "run" methods."""

import typing as t

o = t.TypeVar("o")


def apply(obj: o, method: str) -> o:
    """Return a new object like "o" which has the method string attached."""

    class MockInheritanceClass(obj):
        """Copy of the original class with the new method attribute.

        We can not set the method directly on the original class, because
        it would be used by all the other instances of the class as well.
        """

        _method = method

    MockInheritanceClass.__module__ = obj.__module__
    MockInheritanceClass.__name__ = obj.__name__

    return MockInheritanceClass
