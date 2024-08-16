"""Helpers for the Node Working Directory (NWD)."""

import logging
import os
import pathlib
import shutil
import znflow.utils
import znjson
import json

from .. import config

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

def get_nwd(node: "Node", mkdir: bool = False) -> pathlib.Path:
    """Get the node working directory.

    This is used instead of `node.nwd` because it allows
    for parameters to define if the nwd should be created.

    Attributes
    ----------
    node: Node
        The node instance for which the nwd should be returned.
    mkdir: bool, optional
        If True, the nwd is created if it does not exist.

    """
    try:
        nwd = node.__dict__["nwd"]
    except KeyError:
        if node.name is None:
            raise ValueError("Unable to determine node name.")
        if node.state.remote is None and node.state.rev is None and node.state.state == config.NodeStatusEnum.FINISHED:
            nwd = pathlib.Path("nodes", node.name)
        else:
            try:
                with node.state.fs.open(config.ZNTRACK_FILE_PATH) as f:
                    zntrack_config = json.load(f)
                nwd = zntrack_config[node.name]["nwd"]
                nwd = json.loads(json.dumps(nwd), cls=znjson.ZnDecoder)
            except (FileNotFoundError, KeyError):
                nwd = pathlib.Path("nodes", node.name)
    if mkdir:
        nwd.mkdir(parents=True, exist_ok=True)
    return nwd

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
        else:
            raise ValueError(
                f"replace_nwd_placeholder is not implemented for {type(value)}"
            )