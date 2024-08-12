"""Helpers for the Node Working Directory (NWD)."""

import logging
import os
import pathlib
import shutil

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


def replace_nwd_placeholder(value: str | pathlib.Path, node_wd: pathlib.Path) -> str:
    """Replace the nwd placeholder with the actual nwd."""
    if isinstance(value, str):
        return value.replace(nwd, node_wd.as_posix())
    elif isinstance(value, pathlib.Path):
        return value.as_posix().replace(nwd, node_wd.as_posix())
    else:
        raise ValueError(f"replace_nwd_placeholder is not implemented for {type(value)}")
