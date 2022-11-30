"""Description: ZnTrack custom exceptions."""
import asyncio


class DescriptorMissingError(Exception):
    """Description Missing Exception."""


class DVCProcessError(Exception):
    """DVC specific message for CalledProcessError."""


class DataNotAvailableError(asyncio.InvalidStateError):
    """Access Data that is not available.

    Trying to access e.g. zn.outs that are not computed yet will raise this error
    """


class GraphNotAvailableError(Exception):
    """DVC Graph is not written yet.

    Trying to access graph features such as zn.params or dvc.outs which are not available
    """
