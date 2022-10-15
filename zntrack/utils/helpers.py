def isnode(node, subclass: bool = True) -> bool:
    """Check if node contains a Node instance or class

    Attributes
    ----------
    subclass: bool, default=True
        Allow instances and class definitions. If False, only allow instances
    """
    from zntrack.core.base import Node

    if isinstance(node, (list, tuple)):
        for x in node:
            if not isnode(x, subclass=subclass):
                return False
        return True
    else:
        try:
            if subclass:
                if isinstance(node, Node) or issubclass(node, Node):
                    return True
            elif isinstance(node, Node):
                return True
        except TypeError:
            pass
    return False
