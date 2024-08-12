"""Helpers for the Node Working Directory (NWD)."""

import logging
import os
import pathlib
import shutil

from znflow.utils import IterableHandler

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


class ReplaceNWD(IterableHandler):
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
        else:
            raise ValueError(
                f"replace_nwd_placeholder is not implemented for {type(value)}"
            )
