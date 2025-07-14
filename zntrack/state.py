import contextlib
import dataclasses
import datetime
import importlib.metadata
import json
import pathlib
import tempfile
import typing as t
import warnings

import dvc.api
import dvc.repo
import dvc.stage.serialize
from dvc.utils import dict_sha256
from fsspec.implementations.local import LocalFileSystem
from fsspec.spec import AbstractFileSystem

from zntrack.config import NodeStatusEnum
from zntrack.group import Group
from zntrack.plugins import ZnTrackPlugin
from zntrack.utils.node_wd import get_nwd

if t.TYPE_CHECKING:
    from zntrack import Node

PLUGIN_LIST = list[t.Type[ZnTrackPlugin]]
PLUGIN_DICT = dict[str, ZnTrackPlugin]


@dataclasses.dataclass(frozen=True)
class NodeStatus:
    """Node status object.

    Parameters
    ----------
    remote : str, optional
        The repository remote, e.g. the URL of the git repository.
    rev : str, optional
        The revision of the repository, e.g. the git commit hash.
    run_count : int
        How often this Node has been run.
        Only incremented when the Node is restarted.
    state : NodeStatusEnum
        The state of the Node.
    lazy_evaluation : bool
        Whether to load fields lazily.
    tmp_path : pathlib.Path, optional
        The temporary path when using 'use_tmp_path'.
    node : Node, optional
        The Node object.
    plugins : dict[str, ZnTrackPlugin], optional
        Active plugins. In addition to the default plugins, MLFLow or AIM plugins will
        be added here.
    group : Group, optional
        The group of the Node.
    run_time : datetime.timedelta, optional
        The total run time of the Node.
    name: str
        The name of the Node.
    nwd: pathlib.Path
        The node working directory.
    restarted: bool
        Whether the Node was restarted and has been run at least once before.
    path: str
        The path to the directory where the ``zntrack.json`` file is located.
    """

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
    run_time: datetime.timedelta | None = None
    path: pathlib.Path = dataclasses.field(default_factory=pathlib.Path)
    lockfile: dict | None = None
    fs: AbstractFileSystem | None = dataclasses.field(
        default_factory=LocalFileSystem, repr=False, compare=False, hash=False
    )
    # TODO: move node name and nwd to here as well

    @property
    def name(self) -> str:
        return self.node.name

    @property
    def nwd(self):
        if self.tmp_path is not None:
            return self.tmp_path
        return self.path / get_nwd(self.node)

    @property
    def dvc_fs(self) -> dvc.api.DVCFileSystem:
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
    def use_tmp_path(self, path: pathlib.Path | None = None) -> t.Iterator[pathlib.Path]:
        """Load the data for ``*_path`` into a temporary directory.

        If you can not use ``node.state.fs.open`` you can use
        this as an alternative. This will load the data into
        a temporary directory and then delete it afterwards.
        The respective paths ``node.*_path`` will be replaced
        automatically inside the context manager.

        This is only set, if either ``remote`` or ``rev`` are set.
        Otherwise, the data will be loaded from the current directory.

        Examples
        --------

        >>> import zntrack
        >>> from pathlib import Path
        >>>
        >>> class MyNode(zntrack.Node):
        ...     outs_path: Path = zntrack.outs_path(zntrack.nwd / "file.txt")
        ...
        ...     def run(self):
        ...         self.outs_path.parent.mkdir(parents=True, exist_ok=True)
        ...         self.outs_path.write_text("Hello World!")
        ...
        ...     @property
        ...     def data(self):
        ...         with self.state.use_tmp_path():
        ...             with open(self.outs_path) as f:
        ...                 return f.read()
        ...
        >>> # build and run the graph and make multiple commits.
        >>> # the `use_tmp_path` ensures that the correct version
        >>> # of the file is loaded in the temporary directory and
        >>> # the `self.outs_path` is updated accordingly.
        >>>
        >>> zntrack.from_rev("MyNode", rev="HEAD").data
        >>> zntrack.from_remote("MyNode", rev="HEAD~1").data

        """
        if path is not None:
            raise NotImplementedError("Custom paths are not implemented yet.")

        # This feature is only required when the load
        #  is loaded, not when it is saved/executed
        if self.remote is None and self.rev is None:
            warnings.warn(
                "The temporary path is not used when neither remote or rev are set."
                "Consider checking for `self.state.remote` and `self.state.rev` when"
                "using `with node.state.use_tmp_path(): ...` ."
            )
            yield pathlib.Path.cwd()
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            self.node.__dict__["state"]["tmp_path"] = pathlib.Path(tmpdir)
            try:
                yield pathlib.Path(tmpdir)
            finally:
                self.node.__dict__["state"].pop("tmp_path")

    def get_stage(self) -> dvc.stage.Stage:
        """Access to the internal dvc.repo api."""
        stage = next(iter(self.dvc_fs.repo.stage.collect(self.name)))
        if self.rev is None and self.remote is None:
            # If we want to look at the current workspace result, we need to
            # load all the information, not just dvc.yaml
            stage.save(allow_missing=True, run_cache=False)
        return stage

    def get_stage_lock(self) -> dict:
        """Access to the internal dvc.repo api."""
        stage = self.get_stage()
        return dvc.stage.serialize.to_single_stage_lockfile(stage)

    def get_stage_hash(self, include_outs: bool = False) -> str:
        """Get the hash of the stage."""
        stage_lock = self.get_stage_lock()

        if include_outs:
            return dict_sha256(stage_lock)
        else:
            filtered_lock = {
                k: v for k, v in stage_lock.items() if k in ["cmd", "deps", "params"]
            }
            return dict_sha256(filtered_lock)

    def to_dict(self) -> dict:
        """Convert the NodeStatus to a dictionary."""
        content = dataclasses.asdict(self)
        content.pop("node")
        return content

    def get_field(self, attribute: str) -> dataclasses.Field:
        fields = dataclasses.fields(self.node)
        for field in fields:
            if field.name == attribute:
                return field
        else:
            raise AttributeError(f"Unable to locate '{attribute}' in {self.node}.")

    def add_run_time(self, run_time: datetime.timedelta) -> None:
        """Add the run time to the node."""
        if self.run_time is None:
            self.node.__dict__["state"]["run_time"] = run_time
        else:
            self.node.__dict__["state"]["run_time"] += run_time

    def increment_run_count(self) -> None:
        self.node.__dict__["state"]["run_count"] = self.run_count + 1

    def set_lockfile(self, lockfile: dict) -> None:
        """Set the lockfile for the node."""
        self.node.__dict__["state"]["lockfile"] = lockfile

    def save_node_meta(self) -> None:
        node_meta_content = {
            "uuid": str(self.node.uuid),
            "run_count": self.run_count,
            "zntrack_version": importlib.metadata.version("zntrack"),
        }

        if self.run_time is not None:
            node_meta_content["run_time"] = self.run_time.total_seconds()
        if self.lockfile is not None:
            node_meta_content["lockfile"] = self.lockfile

        with contextlib.suppress(importlib.metadata.PackageNotFoundError):
            module = self.node.__module__.split(".")[0]
            node_meta_content["package_version"] = importlib.metadata.version(module)
        self.nwd.mkdir(parents=True, exist_ok=True)
        (self.nwd / "node-meta.json").write_text(json.dumps(node_meta_content, indent=2))

    @property
    def changed(self) -> bool:
        stage = self.get_stage()
        with stage.repo.lock:
            return stage.changed()
