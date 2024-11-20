# an exception if one tries to access node - data from a node that has not been loaded yet.
class ZnTrackError(Exception):
    """Base class for exceptions in this module."""

    pass


class InvalidOptionError(ZnTrackError, AttributeError):
    """Raised when using an invalid ZnTrackOption for a task."""
