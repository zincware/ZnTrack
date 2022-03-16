from zntrack.core.base import Node


def isnode(node) -> bool:
    """Check if node contains a Node instance or class"""
    if isinstance(node, (list, tuple)):
        return any([isnode(x) for x in node])
    else:
        try:
            if isinstance(node, Node) or issubclass(node, Node):
                return True
        except TypeError:
            pass
    return False
