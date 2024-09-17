import contextlib
import dataclasses
import pathlib
import tempfile
import typing as t

import dvc.api
import dvc.repo
import dvc.stage.serialize
from dvc.utils import dict_sha256
from fsspec.implementations.local import LocalFileSystem
from fsspec.spec import AbstractFileSystem

from zntrack.config import (
    NOT_AVAILABLE,
    ZNTRACK_LAZY_VALUE,
    ZNTRACK_OPTION,
    NodeStatusEnum,
    ZnTrackOptionEnum,
)
from zntrack.exceptions import InvalidOptionError
from zntrack.group import Group
from zntrack.plugins import ZnTrackPlugin

if t.TYPE_CHECKING:
    from zntrack import Node

PLUGIN_LIST = list[t.Type[ZnTrackPlugin]]
PLUGIN_DICT = dict[str, ZnTrackPlugin]


@dataclasses.dataclass(frozen=True)
class NodeStatus:
    remote: str | None = None
    rev: str | None = None
    run_count: int = 0
    state: NodeStatusEnum = NodeStatusEnum.CREATED
    lazy_evaluation: bool = True
    tmp_path: pathlib.Path | None = None
    node: "Node|None" = dataclasses.field(
        default=None, repr=False, compare=False, hash=False
    )
    plugins: PLUGIN_DICT = dataclasses.field(
        default_factory=dict, compare=False, repr=False
    )
    group: Group | None = None
    # TODO: move node name and nwd to here as well

    @property
    def name(self) -> str:
        return self.node.name

    @property
    def fs(self) -> AbstractFileSystem:
        """Get the file system of the Node."""
        if self.remote is None and self.rev is None:
            return LocalFileSystem()
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
        with dvc.repo.Repo(remote=self.remote, rev=self.rev) as repo:
            stage = repo.stage.collect(self.name)[0]
            if self.rev is None:
                # If the rev is not None, we don't need this but get:
                # AttributeError: 'Repo' object has no attribute 'stage_cache'
                stage.save(allow_missing=True, run_cache=False)
            return stage

    def get_stage_lock(self) -> dict:
        """Access to the internal dvc.repo api."""
        stage = self.get_stage()
        return dvc.stage.serialize.to_single_stage_lockfile(stage)

    def get_stage_hash(self, include_outs: bool = False) -> str:
        """Get the hash of the stage."""
        if include_outs:
            raise NotImplementedError("Include outs is not implemented yet.")
        try:
            # I do not understand what is goind on here?
            (
                self.node.nwd / "node-meta.json"
            ).touch()  # REMOVE!!!! node-meta might exist, do not remove!!
            stage_lock = self.get_stage_lock()
        finally:
            content = (self.node.nwd / "node-meta.json").read_text()
            if content == "":
                (self.node.nwd / "node-meta.json").unlink()

        filtered_lock = {
            k: v for k, v in stage_lock.items() if k in ["cmd", "deps", "params"]
        }
        return dict_sha256(filtered_lock)

    def to_dict(self) -> dict:
        """Convert the NodeStatus to a dictionary."""
        content = dataclasses.asdict(self)
        content.pop("node")
        return content

    def extend_plots(self, attribute: str, data: dict):
        # if isintance(target, str): ...
        # TODO: how to check if something has already been written when using extend_plot on
        # some plots but not on others in the final saving step?

        # TODO: check that the stage hash is the same if metrics are set or not
        # TODO: test get_stage_hash with params / metrics / plots / outs / out_path / ...
        import pandas as pd

        fields = dataclasses.fields(self.node)
        for field in fields:
            if field.name == attribute:
                option_type = field.metadata.get(ZNTRACK_OPTION)
                if option_type == ZnTrackOptionEnum.PLOTS:
                    break
                else:
                    raise InvalidOptionError(
                        f"Can not use self.{attribute} with type {option_type} for 'plots'."
                    )
        else:
            raise InvalidOptionError(f"Unable to find 'self.{attribute}' in {self.node}.")

        target = getattr(self.node, attribute)
        if target is ZNTRACK_LAZY_VALUE or target is NOT_AVAILABLE:
            target = pd.DataFrame()
        df = pd.concat([target, pd.DataFrame([data])], ignore_index=True, axis=0)
        if "step" not in df.columns:
            df.index.name = "step"
        setattr(self.node, attribute, df)
        for plugin in self.plugins.values():
            plugin.extend_plots(attribute, data, reference=df)

    def get_field(self, attribute: str) -> dataclasses.Field:
        fields = dataclasses.fields(self.node)
        for field in fields:
            if field.name == attribute:
                return field
        else:
            raise AttributeError(f"Unable to locate '{attribute}' in {self.node}.")
