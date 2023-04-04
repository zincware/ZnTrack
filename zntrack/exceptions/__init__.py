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
