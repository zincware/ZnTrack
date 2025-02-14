"""Zntrack apply module for custom "run" methods."""

import typing as t

o = t.TypeVar("o")


def apply(obj: o, method: str) -> o:
    """Update the default ``run`` method of ``zntrack.Node``.

    Parameters
    ----------
    obj : zntrack.Node
        The node to copy and update the ``run`` method.
    method : str
        The new method to use instead of the default ``run`` method.

    Returns
    -------
    zntrack.Node
        A new class which uses the new method instead of the default ``run`` method.

    Examples
    --------
    >>> import zntrack
    >>> class MyNode(zntrack.Node):
    ...     outs: str = zntrack.outs()
    ...
    ...     def run(self):
    ...         self.outs = "Hello, World!"
    ...
    ...     def my_run(self):
    ...         self.outs = "Hello, Custom World!"
    ...
    >>> OtherMyNode = zntrack.apply(MyNode, "my_run")
    >>> with zntrack.Project() as proj:
    ...     a = MyNode()
    ...     b = OtherMyNode()
    >>> proj.repro()
    >>> a.outs
    'Hello, World!'
    >>> b.outs
    'Hello, Custom World!'
    """

    if not hasattr(obj, method):
        raise AttributeError(f"The object does not have the requested method '{method}'.")

    class MockInheritanceClass(obj):
        """Copy of the original class with the new method attribute.

        We can not set the method directly on the original class, because
        it would be used by all the other instances of the class as well.
        """

        _method = method

    MockInheritanceClass.__module__ = obj.__module__
    MockInheritanceClass.__name__ = obj.__name__

    return MockInheritanceClass
