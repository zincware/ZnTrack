import dataclasses
import pathlib
import typing as t

import znfields
import znflow


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
