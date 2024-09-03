import contextlib
import dataclasses
import json
import os
import pathlib
import tempfile
import typing as t

import dvc.api
import dvc.repo
import dvc.stage
import dvc.stage.serialize
import typing_extensions as te
import znfields
import znflow
from dvc.utils import dict_sha256

from .config import ZNTRACK_LAZY_VALUE, NodeStatusEnum, NOT_AVAILABLE
from .utils.import_handler import import_handler
from .utils.node_wd import get_nwd

try:
    from typing import dataclass_transform
except ImportError:
    from typing_extensions import dataclass_transform

T = t.TypeVar("T", bound="Node")


@dataclasses.dataclass(frozen=True)
class NodeStatus:
    name: str | None
    remote: str | None
    rev: str | None
    run_count: int = 0
    state: NodeStatusEnum = NodeStatusEnum.CREATED
    lazy_evaluation: bool = True
    tmp_path: pathlib.Path | None = None
    node: "Node|None" = dataclasses.field(
        default=None, repr=False, compare=False, hash=False
    )
    group: tuple[str] | None = None
    # TODO: move node name and nwd to here as well

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

    @contextlib.contextmanager
    def use_tmp_path(self, path: pathlib.Path | None = None) -> t.Iterator[None]:
        """Load the data for '*_path' into a temporary directory.

        If you can not use 'node.state.fs.open' you can use
        this as an alternative. This will load the data into
        a temporary directory and then delete it afterwards.
        The respective paths 'node.*_path' will be replaced
        automatically inside the context manager.

        This is only set, if either 'remote' or 'rev' are set.
        Otherwise, the data will be loaded from the current directory.
        """
        if path is not None:
            raise NotImplementedError("Custom paths are not implemented yet.")

        with tempfile.TemporaryDirectory() as tmpdir:
            self.node.__dict__["state"]["tmp_path"] = pathlib.Path(tmpdir)
            try:
                yield
            finally:
                self.node.__dict__["state"].pop("tmp_path")

    def get_stage(self) -> dvc.stage.PipelineStage:
        """Access to the internal dvc.repo api."""
        remote = self.remote if self.remote != "." else None
        with dvc.repo.Repo(remote=remote, rev=self.rev) as repo:
            stage = repo.stage.collect(self.name)[0]
            stage.save(allow_missing=True)
            return stage

    def get_stage_lock(self) -> dict:
        """Access to the internal dvc.repo api."""
        stage = self.get_stage()
        return dvc.stage.serialize.to_single_stage_lockfile(stage)

    def get_stage_hash(self, include_outs: bool = False) -> str:
        """Get the hash of the stage."""
        if include_outs:
            raise NotImplementedError("Include outs is not implemented yet.")
        stage_lock = self.get_stage_lock()
        filtered_lock = {
            k: v for k, v in stage_lock.items() if k in ["cmd", "deps", "params"]
        }
        return dict_sha256(filtered_lock)

    @property
    def plugins(self) -> dict:
        """Get the plugins of the node."""
        plugins = os.environ.get(
            "ZNTRACK_PLUGINS", "zntrack.plugins.dvc_plugin.DVCPlugin"
        )
        plugins = plugins.split(",")

        plugins = [import_handler(plugin) for plugin in plugins]

        return {plugin.__name__: plugin(self.node) for plugin in plugins}

    def to_dict(self) -> dict:
        """Convert the NodeStatus to a dictionary."""
        content = dataclasses.asdict(self)
        content.pop("node")
        return content


@dataclass_transform()
@dataclasses.dataclass(kw_only=True)
class Node(znflow.Node, znfields.Base):
    """A Node."""

    name: str | None = None

    _protected_ = znflow.Node._protected_ + ["nwd", "name", "state"]

    def __post_init__(self):
        if self.name is None:
            # automatic node names expectes the name to be None when
            # exiting the graph context.
            if not znflow.get_graph() is not znflow.empty_graph:
                self.name = self.__class__.__name__

    def run(self):
        raise NotImplementedError

    def save(self):
        for plugin in self.state.plugins.values():
            for field in dataclasses.fields(self):
                if getattr(self, field.name) in [ZNTRACK_LAZY_VALUE, NOT_AVAILABLE]:
                    raise ValueError(
                        f"Field '{field.name}' is not set. Please set it before saving."
                    )
                plugin.save(field)
        _ = self.state
        self.__dict__["state"]["state"] = NodeStatusEnum.FINISHED

    def __init_subclass__(cls):
        return dataclasses.dataclass(cls)

    @property
    def nwd(self) -> pathlib.Path:
        return get_nwd(self, mkdir=True)

    @classmethod
    def from_rev(
        cls: t.Type[T],
        name: str | None = None,
        remote: str | None = ".",
        rev: str | None = None,
        running: bool = False,
        lazy_evaluation: bool = True,
        **kwargs,
    ) -> T:
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
        instance.__dict__["state"] = NodeStatus(
            name=name,
            remote=remote,
            rev=rev,
            run_count=run_count,
            state=NodeStatusEnum.RUNNING if running else NodeStatusEnum.FINISHED,
            lazy_evaluation=lazy_evaluation,
            node=None,
        ).to_dict()

        if not instance.state.lazy_evaluation:
            for field in dataclasses.fields(cls):
                _ = getattr(instance, field.name)

        return instance

    @property
    def state(self) -> NodeStatus:
        if "state" not in self.__dict__:
            self.__dict__["state"] = NodeStatus(
                name=self.name,
                remote=".",
                rev=None,
                run_count=0,
                state=NodeStatusEnum.CREATED,
                lazy_evaluation=True,
                node=None,
            ).to_dict()

        return NodeStatus(**self.__dict__["state"], node=self)

    def update_run_count(self):
        try:
            self.__dict__["state"]["run_count"] += 1
        except KeyError:
            self.__dict__["state"] = NodeStatus(
                name=self.name,
                remote=".",
                rev=None,
                run_count=1,
                state=NodeStatusEnum.RUNNING,
                lazy_evaluation=True,
                node=None,
            ).to_dict()
        (self.nwd / "node-meta.json").write_text(
            json.dumps({"uuid": str(self.uuid), "run_count": self.state.run_count})
        )

    @te.deprecated("loading is handled automatically via lazy evaluation")
    def load(self):
        pass
