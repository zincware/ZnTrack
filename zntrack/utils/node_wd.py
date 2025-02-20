"""Helpers for the Node Working Directory (NWD)."""

import logging
import os
import pathlib
import shutil
import typing as t
import warnings

import znflow.utils

from zntrack.add import DVCImportPath
from zntrack.config import NWD_PATH

if t.TYPE_CHECKING:
    from zntrack import Node


log = logging.getLogger(__name__)


class _NWD(str):
    """String that allows for pathlib like truediv operation."""

    def __truediv__(self, other) -> pathlib.Path:
        return pathlib.Path(self, other)


nwd = _NWD("$nwd$")


def move_nwd(target: pathlib.Path, destination: pathlib.Path) -> None:
    """Move files from 'target' to 'destination'."""
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(target, destination, copy_function=os.link)
    shutil.rmtree(target)


def get_nwd(node: "Node") -> pathlib.Path:
    """Get the node working directory.

    Arguments:
    ---------
    node: Node
        The node instance for which the nwd should be returned.
    """
    try:
        return node.__dict__["nwd"]
    except KeyError:
        warnings.warn(
            "Using the NWD outside a project context"
            " can not guarantee unique directories."
        )
        return pathlib.Path(NWD_PATH, node.__class__.__name__)


class NWDReplaceHandler(znflow.utils.IterableHandler):
    """Replace the nwd placeholder with the actual nwd."""

    def default(self, value, **kwargs):
        """Replace the nwd placeholder with the actual nwd."""
        if isinstance(value, str):
            if value == nwd:
                # nwd is of type str but will be converted to pathlib.Path
                return pathlib.Path(kwargs["nwd"])
            return value.replace(nwd, pathlib.Path(kwargs["nwd"]).as_posix())
        elif isinstance(value, pathlib.Path):
            return pathlib.Path(
                value.as_posix().replace(nwd, pathlib.Path(kwargs["nwd"]).as_posix())
            )
        elif value is None:
            return value
        elif isinstance(value, DVCImportPath):
            # with DVCImportPath, we do not expect the nwd placeholder
            return value.path
        else:
            raise ValueError(
                f"replace_nwd_placeholder is not implemented for {type(value)}"
            )
