"""Helpers for the Node Working Directory (NWD)."""

import logging
import pathlib
import typing

log = logging.getLogger(__name__)


class _NWD(str):
    """String that allows for pathlib like truediv operation."""

    def __truediv__(self, other) -> pathlib.Path:
        return pathlib.Path(self, other)


nwd = _NWD("$nwd$")


def replace_nwd_placeholder(  # noqa: C901
    path: typing.Union[str, pathlib.Path, tuple, list],
    node_working_directory: typing.Union[str, pathlib.Path],
):
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
    replaced: bool
        Whether the placeholder was found and replaced or not


    """
    if path is None:
        return path, False
    if isinstance(path, (tuple, list)):
        # This could be cleaned up
        paths = []
        replace = False
        for _path in path:
            x, y = replace_nwd_placeholder(_path, node_working_directory)
            paths.append(x)
            if y is True:
                replace = True
        return paths, replace

    _type = "str"
    if isinstance(path, pathlib.Path):
        _type = "path"
        _path = path.as_posix()
    else:
        _path = path

    try:
        replace = nwd in _path
    except TypeError:
        # argument of type <Node> is not iterable. This can happen when you use
        #  e.g. dvc.deps(Node) (deprecated)
        return path, False
    if not replace:
        return path, False

    if isinstance(node_working_directory, pathlib.Path):
        node_working_directory = node_working_directory.as_posix()

    _path = _path.replace(nwd, node_working_directory)

    if _type == "path":
        _path = pathlib.Path(_path)

    log.info(f"Replacing {nwd} with {node_working_directory} -> {_path}")
    return _path, replace
