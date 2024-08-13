import dataclasses
import pathlib
import typing as t

import dvc.api
import znfields
import znflow

from .config import ZNTRACK_LAZY_VALUE, ZNTRACK_SAVE_FUNC


@dataclasses.dataclass(frozen=True)
class NodeStatus:
    remote: str = "."
    rev: str | None = None
    run_counter: int = 0

    @property
    def fs(self) -> dvc.api.DVCFileSystem:
        """Get the file system of the Node."""
        return dvc.api.DVCFileSystem(
            url=self.remote,
            rev=self.rev,
        )

    @property
    def restarted(self) -> bool:
        """Whether the node was restarted."""
        return self.run_counter > 1


@t.dataclass_transform()
@dataclasses.dataclass(kw_only=True)
class Node(znflow.Node, znfields.Base):
    """A Node."""

    name: str | None = None

    _protected_ = znflow.Node._protected_ + ["nwd", "name"]

    def run(self):
        raise NotImplementedError

    def save(self):
        for field in dataclasses.fields(self):
            func = field.metadata.get(ZNTRACK_SAVE_FUNC, None)
            if callable(func):
                func(self, field.name)

    def __init_subclass__(cls):
        return dataclasses.dataclass(cls)

    @property
    def nwd(self) -> pathlib.Path:
        node_wd = pathlib.Path(f"nodes/{self.name}/")
        if not node_wd.exists():
            node_wd.mkdir(parents=True)
        return node_wd

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
        instance = cls(**lazy_values)
        instance.__dict__["state"] = {"remote": remote, "rev": rev}
        # TODO: try reading node-meta, if available set run_counter

        return instance

    @property
    def state(self) -> NodeStatus:
        if "state" not in self.__dict__:
            self.__dict__["state"] = {}
        return NodeStatus(**self.__dict__["state"])
