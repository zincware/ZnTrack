"""All ZnTrack exceptions."""


class NodeNotAvailableError(Exception):
    """Raised when a node is not available."""

    def __init__(self, arg):
        """Initialize the exception.

        Parameters
        ----------
        arg : str|Node
            Custom Error message or Node that is not available.
        """
        if isinstance(arg, str):
            super().__init__(arg)
        else:
            # assume arg is a Node
            super().__init__(f"Node {arg.name} is not available.")


class ZnNodesOnGraphError(Exception):
    """Raised when a node is not available."""

    def __init__(self, node, field, instance):
        """Initialize the exception.

        Parameters
        ----------
        node : Node
            The node that is passed to 'zn.nodes()'
        field : Field
            The 'zn.nodes' field
        instance : Node
            The node that contains the 'zn.nodes' field
        """
        msg = (
            f"Can not set '{field.name}' of Node<'{instance.name}'> to"
            f" Node<'{node.name}'>. The  Node<'{node.name}'> is already on the graph."
            " Nodes that are passed to 'zn.nodes' must be defined outside the graph:"
        )

        msg += f"""
        >>> {node.name} = ...
        >>> with project:
        >>>    {instance.name}.{field.name} = {node.name}
        """

        super().__init__(msg)
