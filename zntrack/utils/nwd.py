"""Helpers for the Node Working Directory (NWD)."""

import functools
import logging
import pathlib
import typing

log = logging.getLogger(__name__)


class _NWD(str):
    """String that allows for pathlib like truediv operation."""

    def __truediv__(self, other) -> pathlib.Path:
        return pathlib.Path(self, other)


nwd = _NWD("$nwd$")


@functools.singledispatch
def replace_nwd_placeholder(
    path,
    node_working_directory: typing.Union[str, pathlib.Path],
) -> str:
    """Replace the nwd placeholder in the path with the actual node_working_directory.

    Parameters
    ----------
    path: str|Path|list|tuple
        The path containing a nwd placeholder to replace
    node_working_directory: str
        The replacement for the nwd placeholder

    Returns
    -------
    path: obj
        Object of the same type as the input (tuples -> list conversion) with the
        placeholder replaced by node_working_directory. Additionally, a boolean value
    """
    raise ValueError(f"replace_nwd_placeholder is not implemented for {type(path)}")


@replace_nwd_placeholder.register
def _(path: None, node_working_directory) -> None:
    """Replace nothing."""
    return path


@replace_nwd_placeholder.register
def _(path: str, node_working_directory) -> typing.Union[str, pathlib.Path]:
    """Main function to replace $nwd$ with 'nwd'."""
    if path == nwd:
        return node_working_directory
    return path.replace(nwd, pathlib.Path(node_working_directory).as_posix())


@replace_nwd_placeholder.register
def _(path: list, node_working_directory) -> list:
    """Replace list."""
    return [replace_nwd_placeholder(x, node_working_directory) for x in path]


@replace_nwd_placeholder.register
def _(path: tuple, node_working_directory) -> tuple:
    """Replace tuple."""
    return tuple(replace_nwd_placeholder(x, node_working_directory) for x in path)


@replace_nwd_placeholder.register
def _(path: pathlib.Path, node_working_directory) -> pathlib.Path:
    """Replace pathlib.Path."""
    return pathlib.Path(replace_nwd_placeholder(path.as_posix(), node_working_directory))
