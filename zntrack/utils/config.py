"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Configuration File for ZnTrack
"""
import enum
import logging
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Collection of Node configurations

    Attributes
    ----------
    nb_name: str
        Name of the JupyterNotebook, if the Nodes are defined in a Notebook
    nb_class_path: Path
        The path where jupyter notebooks should write the *.py
    lazy: bool, default = True
        Use lazy loading for Node.load(). This means that all ZnTrackOptions are only
        loaded from files when they are first accessed.
    allow_empty_loading: bool
        Allow "Node.load(lazy=False)" even if nothing can be loaded, e.g.
        zntrack.json / params.yaml does not exist or does not contain data
        for the respective Node.
    log_level: int, default = logging.WARNING
        The log level to be used in the ZnTrack stdout logger.
        The default log level (WARNING) will provide sufficient information for most
        runs. If you encounter any issues you can set it to logging.INFO for more in-depth
        information. DEBUG level can produce a lot of useful information for more complex
        issues.
    """

    nb_name: str = None
    nb_class_path: Path = Path("src")
    lazy: bool = True
    allow_empty_loading: bool = False
    _log_level: int = field(default=logging.WARNING, init=False, repr=True)

    @property
    def log_level(self):
        return self._log_level

    @log_level.setter
    def log_level(self, value):
        """Update the loglevel of the ZnTrack logger"""
        self._log_level = value
        logger = logging.getLogger("zntrack")
        logger.setLevel(self._log_level)


@dataclass(frozen=True)
class Files:
    """Important File paths for ZnTrack to work

    Notes
    ------
    Currently frozen because changing the value is not tested.
    """

    zntrack: Path = Path("zntrack.json")
    params: Path = Path("params.yaml")


class ZnTypes(enum.Enum):
    """Collection of ZnTrack Types to identify descriptors beyond their dvc option

    Attributes
    ----------
    results: most zn.<options> like zn.outs() / zn.metrics() use this one
    """

    DEPS = enum.auto()
    DVC = enum.auto()
    METADATA = enum.auto()
    # method = enum.auto()
    PARAMS = enum.auto()
    ITERABLE = enum.auto()
    RESULTS = enum.auto()


FILE_DVC_TRACKED = [ZnTypes.DVC]
# if the getattr(instance, self.name) is an affected file,
# e.g. the dvc.<outs> is a file / list of files
VALUE_DVC_TRACKED = [ZnTypes.RESULTS, ZnTypes.METADATA]
# if the internal file,
# e.g. in the case of zn.outs() like nodes/<node_name>/outs.json is an affected file


config = Config()
