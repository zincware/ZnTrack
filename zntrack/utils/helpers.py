def isnode(node) -> bool:
    """Check if node contains a Node instance or class"""
    from zntrack.core.base import Node

    if isinstance(node, (list, tuple)):
        return any([isnode(x) for x in node])
    else:
        try:
            if isinstance(node, Node) or issubclass(node, Node):
                return True
        except TypeError:
            pass
    return False
