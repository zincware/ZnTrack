"""Base class for zntrack plugins."""

import abc
import dataclasses
import typing as t

from zntrack.config import NOT_AVAILABLE, ZNTRACK_LAZY_VALUE
from zntrack.exceptions import NodeNotAvailableError

if t.TYPE_CHECKING:
    from zntrack import Node


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
        raise NodeNotAvailableError(f"Node '{self.name}' is not available")

    return getattr(self, name)
