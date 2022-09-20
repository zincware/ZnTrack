def isnode(node) -> bool:
    """Check if node contains a Node instance or class"""
    from zntrack.core.base import Node

    if isinstance(node, (list, tuple)):
        for x in node:
            if isnode(x):
                return True
        return False
    else:
        try:
            if isinstance(node, Node) or issubclass(node, Node):
                return True
        except TypeError:
            pass
    return False
