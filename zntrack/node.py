import dataclasses
import pathlib
import typing as t

import znfields
import znflow


@t.dataclass_transform()
class Node(znflow.Node, znfields.Base):
    """A Node."""

    def __init_subclass__(cls):
        return dataclasses.dataclass(cls)

    @property
    def name(self) -> str:
        return self.uuid.hex[:4]

    @property
    def nwd(self) -> pathlib.Path:
        return pathlib.Path(f"nodes/{self.name}/")
