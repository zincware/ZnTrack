"""Description: Configuration File for ZnTrack"""
import dataclasses
import logging
from pathlib import Path


@dataclasses.dataclass
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
    _log_level: int = dataclasses.field(default=logging.WARNING, init=False, repr=True)

    @property
    def log_level(self):
        return self._log_level

    @log_level.setter
    def log_level(self, value):
        """Update the loglevel of the ZnTrack logger"""
        self._log_level = value
        logger = logging.getLogger("zntrack")
        logger.setLevel(self._log_level)


@dataclasses.dataclass(frozen=True)
class Files:
    """Important File paths for ZnTrack to work

    Notes
    ------
    Currently frozen because changing the value is not tested.
    """

    zntrack: Path = Path("zntrack.json")
    params: Path = Path("params.yaml")


config = Config()
