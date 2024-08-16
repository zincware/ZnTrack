import dataclasses
import json
import pathlib
import typing as t

import dvc.api
import znfields
import znflow

from .config import ZNTRACK_LAZY_VALUE, ZNTRACK_SAVE_FUNC, NodeStatusEnum


@dataclasses.dataclass(frozen=True)
class NodeStatus:
    remote: str = "."
    rev: str | None = None
    run_count: int = 0
    state: NodeStatusEnum = NodeStatusEnum.CREATED

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
        return self.run_count > 1


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
        # we assume that after one calls "save" the node is finished
        self.__dict__["state"]["state"] = NodeStatusEnum.FINISHED

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
        remote: str | None = ".",
        rev: str | None = None,
        running: bool = False,
        **kwargs,
    ) -> "Node":
        if name is None:
            name = cls.__name__
        lazy_values = {}
        for field in dataclasses.fields(cls):
            lazy_values[field.name] = ZNTRACK_LAZY_VALUE

        lazy_values["name"] = name
        instance = cls(**lazy_values)

        try:
            with instance.state.fs.open(instance.nwd / "node-meta.json") as f:
                content = json.load(f)
                run_count = content["run_count"]
        except FileNotFoundError:
            run_count = 0

        # TODO: check if the node is finished or not.
        instance.__dict__["state"] = {
            "remote": remote,
            "rev": rev,
            "run_count": run_count,
            "state": NodeStatusEnum.RUNNING if running else NodeStatusEnum.FINISHED,
        }
        # TODO: try reading node-meta, if available set run_count

        return instance

    @property
    def state(self) -> NodeStatus:
        if "state" not in self.__dict__:
            self.__dict__["state"] = {}
        return NodeStatus(**self.__dict__["state"])

    def update_run_count(self):
        try:
            self.__dict__["state"]["run_count"] += 1
        except KeyError:
            self.__dict__["state"] = {"run_count": 1, "state": NodeStatusEnum.RUNNING, "remote": ".", "rev": None}
        (self.nwd / "node-meta.json").write_text(
            json.dumps({"uuid": str(self.uuid), "run_count": self.state.run_count})
        )
        
    def load(self):
        raise NotImplementedError
