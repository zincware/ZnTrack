"""Base class for zntrack plugins."""

import abc
import dataclasses
import pathlib
import typing as t

import yaml

from zntrack.config import EXP_INFO_PATH, NOT_AVAILABLE, ZNTRACK_LAZY_VALUE

if t.TYPE_CHECKING:
    from zntrack import Node


def _gitignore_file(path: str):
    """Add a path to the .gitignore file if it is not already there."""
    if not pathlib.Path(".gitignore").exists():
        with open(".gitignore", "w") as f:
            f.write(path + "\n")
        return
    with open(".gitignore", "r") as f:
        for line in f:
            if line.strip() == path:
                return
    with open(".gitignore", "a") as f:
        f.write(path + "\n")
    return


def get_exp_info() -> dict:
    if EXP_INFO_PATH.exists():
        return yaml.safe_load(EXP_INFO_PATH.read_text())
    return {}


def set_exp_info(data: dict) -> None:
    EXP_INFO_PATH.write_text(yaml.safe_dump(data))
    _gitignore_file(EXP_INFO_PATH.as_posix())


# TODO: have a dataclass for the base metrics, like hash, name, module, ...
@dataclasses.dataclass
class ZnTrackPlugin(abc.ABC):
    """ABC for writing zntrack plugins."""

    node: "Node"
    _continue_on_error_ = False

    @abc.abstractmethod
    def getter(self, field: dataclasses.Field) -> t.Any:
        """ZnField getter for zntrack options."""
        pass

    @abc.abstractmethod
    def save(self, field: dataclasses.Field) -> None:
        """Save method for zntrack options."""
        pass

    @abc.abstractmethod
    def convert_to_zntrack_json(self, graph) -> t.Any: ...

    @abc.abstractmethod
    def convert_to_dvc_yaml(self) -> t.Any: ...

    @abc.abstractmethod
    def convert_to_params_yaml(self) -> t.Any: ...

    def __enter__(self):
        self.setup()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def setup(self):
        return

    def close(self):
        return

    @classmethod
    def finalize(cls, **kwargs) -> None:
        return


def base_getter(self: "Node", name: str, func: t.Callable):
    if (
        name in self.__dict__
        and self.__dict__[name] is not ZNTRACK_LAZY_VALUE
        and self.__dict__[name] is not NOT_AVAILABLE
    ):
        return self.__dict__[name]

    if name in self.__dict__ and self.__dict__[name] is NOT_AVAILABLE:
        try:
            func(self, name)
        except FileNotFoundError:
            return NOT_AVAILABLE

    try:
        func(self, name)
    except FileNotFoundError:
        return NOT_AVAILABLE

    return getattr(self, name)
