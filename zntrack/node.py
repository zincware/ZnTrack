import dataclasses
import pathlib
import typing as t

import znfields
import znflow

from .config import ZNTRACK_LAZY_VALUE


@t.dataclass_transform()
@dataclasses.dataclass(kw_only=True)
class Node(znflow.Node, znfields.Base):
    """A Node."""

    name: str | None = None

    _protected_ = znflow.Node._protected_ + ["nwd", "name"]

    def __init_subclass__(cls):
        return dataclasses.dataclass(cls)

    @property
    def nwd(self) -> pathlib.Path:
        return pathlib.Path(f"nodes/{self.name}/")

    @classmethod
    def from_rev(
        cls,
        name: str | None = None,
        remote: str | None = None,
        rev: str | None = None,
        **kwargs,
    ) -> "Node":
        if name is None:
            name = cls.__name__
        lazy_values = {}
        for field in dataclasses.fields(cls):
            lazy_values[field.name] = ZNTRACK_LAZY_VALUE

        lazy_values["name"] = name

        return cls(**lazy_values)
