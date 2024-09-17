"""Base class for zntrack plugins."""

import abc
import dataclasses
import typing as t

from zntrack.config import NOT_AVAILABLE, PLUGIN_EMPTY_RETRUN_VALUE, ZNTRACK_LAZY_VALUE
from zntrack.exceptions import NodeNotAvailableError

if t.TYPE_CHECKING:
    from zntrack import Node


# TODO: have a dataclass for the base metrics, like hash, name, module, ...
@dataclasses.dataclass
class ZnTrackPlugin(abc.ABC):
    """ABC for writing zntrack plugins."""

    node: "Node"

    @abc.abstractmethod
    def getter(self, field: dataclasses.Field) -> t.Any:
        """ZnField getter for zntrack options."""
        pass

    @abc.abstractmethod
    def save(self, field: dataclasses.Field) -> None:
        """Save method for zntrack options."""
        pass

    @abc.abstractmethod
    def convert_to_zntrack_json(self) -> t.Any: ...

    @abc.abstractmethod
    def convert_to_dvc_yaml(self) -> t.Any: ...

    @abc.abstractmethod
    def convert_to_params_yaml(self) -> t.Any: ...

    def extend_plots(self, attribute: str, data: dict, reference):
        return PLUGIN_EMPTY_RETRUN_VALUE

    @classmethod
    def finalize(cls, rev: str | None = None, path_to_aim: str = ".") -> None:
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
