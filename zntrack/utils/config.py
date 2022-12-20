"""Description: Configuration File for ZnTrack."""
import contextlib
import dataclasses
import logging
import sys
import typing
from pathlib import Path


@dataclasses.dataclass
class Config:
    """Collection of Node configurations.

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
    interpreter: str|Path, default = None
        Set the Python interpreter to be used for the 'dvc cmd'.
        If None, ZnTrack will try to automatically determine the interpreter.
        Use e.g. `config.interpreter=sys.executable` to use a specific version.
        Note, that changing the command will also affect your graph, and you might
        not be able to use the existing cache.
    dvc_api: bool, default = True
        Use the `dvc.cli.main` function instead of subprocess
    """

    nb_name: str = None
    nb_class_path: Path = Path("src")
    lazy: bool = True
    allow_empty_loading: bool = False
    interpreter: typing.Union[str, Path] = Path(sys.executable).name
    dvc_api: bool = True
    _log_level: int = dataclasses.field(default=logging.INFO, init=False, repr=True)

    @property
    def log_level(self):
        """Get the log level."""
        return self._log_level

    @log_level.setter
    def log_level(self, value):
        """Update the loglevel of the ZnTrack logger."""
        self._log_level = value
        logger = logging.getLogger("zntrack")
        logger.setLevel(self._log_level)

    @contextlib.contextmanager
    def updated_config(self, **kwargs) -> None:
        """Temporarily update the config.

        Yields
        ------
            Environment with temporarily changed config.
        """
        state = {}
        for key, value in kwargs.items():
            state[key] = getattr(self, key)
            setattr(self, key, value)
        try:
            yield
        finally:
            for key, value in state.items():
                setattr(self, key, value)


@dataclasses.dataclass(frozen=True)
class Files:
    """Important File paths for ZnTrack to work.

    Notes
    -----
    Currently frozen because changing the value is not tested.
    """

    zntrack: Path = Path("zntrack.json")
    params: Path = Path("params.yaml")
    dvc: Path = Path("dvc.yaml")


config = Config()
