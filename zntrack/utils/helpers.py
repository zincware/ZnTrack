"""ZnTrack helpers."""
import contextlib


def isnode(node, subclass: bool = True) -> bool:
    """Check if node contains a Node instance or class.

    Attributes
    ----------
    subclass: bool, default=True
        Allow instances and class definitions. If False, only allow instances
    """
    from zntrack.core.base import Node

    if isinstance(node, (list, tuple)):
        return all(isnode(x, subclass=subclass) for x in node)
    with contextlib.suppress(TypeError):
        if subclass:
            if isinstance(node, Node) or issubclass(node, Node):
                return True
        elif isinstance(node, Node):
            return True
    return False
