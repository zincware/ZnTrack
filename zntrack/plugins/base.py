"""Base class for zntrack plugins."""

import abc
import dataclasses
import typing as t

if t.TYPE_CHECKING:
    from zntrack import Node


class ZnTrackPlugin(abc.ABC):
    """ABC for writing zntrack plugins."""

    @abc.abstractmethod
    def getter(self, node: "Node", field: dataclasses.Field) -> t.Any:
        """ZnField getter for zntrack options."""
        pass

    @abc.abstractmethod
    def save(self, node: "Node", field: dataclasses.Field) -> None:
        """Save method for zntrack options."""
        pass
