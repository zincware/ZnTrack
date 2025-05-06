import contextlib
import dataclasses
import datetime
import json
import logging
import pathlib
import typing as t
import uuid
import warnings

import typing_extensions as ty_ex
import znfields
import znflow
from dvc.stage.exceptions import InvalidStageName
from dvc.stage.utils import is_valid_name

from zntrack.group import Group
from zntrack.state import NodeStatus
from zntrack.utils.misc import get_plugins_from_env, nwd_to_name

from .config import NOT_AVAILABLE, NWD_PATH, ZNTRACK_LAZY_VALUE, NodeStatusEnum

try:
    from typing import dataclass_transform
except ImportError:
    from typing_extensions import dataclass_transform

T = t.TypeVar("T", bound="Node")

log = logging.getLogger(__name__)


def _name_setter(self, attr_name: str, value: str) -> None:
    """
    Validates and sets the node name, ensuring uniqueness within the graph.

    Parameters
    ----------
    attr_name : str
        The attribute name to be set.
    value : str
        The desired node name.

    Raises
    ------
    AttributeError
        If the node name is already set and cannot be changed.
    InvalidStageName
        If the given name is invalid.
    ValueError
        If a node with the same name already exists.
    """
    if attr_name in self.__dict__:
        raise AttributeError("Node name cannot be changed.")

    if value is None:
        return

    if not is_valid_name(value):
        raise InvalidStageName

    if "_" in value:
        warnings.warn(
            "Node name should not contain '_'."
            " This character is used for defining groups."
        )
    self.__dict__[attr_name] = value  # only used to check if the name has been set once

    graph = znflow.get_graph()

    # in case the name is set outside the graph
    # (no groups can be active)
    nwd = NWD_PATH / value

    if graph is not znflow.empty_graph:
        name = self.__class__.__name__
        if graph.active_group is None:
            if graph.node_name_counter.get(name, 0) > 0:
                graph.node_name_counter[name] -= 1

            if value in graph.node_name_counter:
                raise ValueError(f"A node with the name '{value}' already exists.")
            graph.node_name_counter[value] = 1
        else:
            group_path = "/".join(graph.active_group.names)
            grp_and_name = f"{group_path}/{name}"

            if graph.node_name_counter.get(grp_and_name, 0) > 0:
                graph.node_name_counter[grp_and_name] -= 1

            node_name = f"{group_path}_{value}"
            if node_name in graph.node_name_counter:
                raise ValueError(f"A node with the name '{node_name}' already exists.")
            graph.node_name_counter[node_name] = 1
            nwd = NWD_PATH / group_path / value

    self.__dict__["nwd"] = nwd


def _name_getter(self, attr_name: str) -> str:
    """Retrieve the name of a node based on the current graph context.

    Parameter
    ---------
        attr_name (str): The attribute name to retrieve.

    Returns
    -------
        str: The resolved node name.

    """

    if self.__dict__.get("nwd") is not None:
        # can not use self.nwd in case of `tmp_path`
        return nwd_to_name(self.__dict__["nwd"])
    else:
        return self.__class__.__name__


@dataclass_transform()
@dataclasses.dataclass(kw_only=True)
class Node(znflow.Node, znfields.Base):
    """A Node."""

    name: str | None = znfields.field(
        default=None, getter=_name_getter, setter=_name_setter
    )
    always_changed: bool = dataclasses.field(default=False, repr=False)

    _protected_ = znflow.Node._protected_ + ["nwd", "name", "state"]

    def __post_init__(self):
        if self.name is None:
            # automatic node names expects the name to be None when
            # exiting the graph context.
            if not znflow.get_graph() is not znflow.empty_graph:
                self.name = self.__class__.__name__

    def _post_load_(self):
        """Called after `from_rev` is called."""
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    def save(self):
        for plugin in self.state.plugins.values():
            with plugin:
                for field in dataclasses.fields(self):
                    value = getattr(self, field.name)
                    if any(value is x for x in [ZNTRACK_LAZY_VALUE, NOT_AVAILABLE]):
                        raise ValueError(
                            f"Field '{field.name}' is not set."
                            " Please set it before saving."
                        )
                    try:
                        plugin.save(field)
                    except Exception as err:  # noqa: E722
                        if plugin._continue_on_error_:
                            warnings.warn(
                                f"Plugin {plugin.__class__.__name__} failed to"
                                f" save field {field.name}."
                            )
                        else:
                            raise err

        _ = self.state
        self.__dict__["state"]["state"] = NodeStatusEnum.FINISHED

    def __init_subclass__(cls):
        return dataclasses.dataclass(cls, kw_only=True)

    @property
    def nwd(self) -> pathlib.Path:
        return self.state.nwd

    @classmethod
    def from_rev(
        cls: t.Type[T],
        name: str | None = None,
        remote: str | None = None,
        rev: str | None = None,
        running: bool = False,
        lazy_evaluation: bool = True,
        path: str | None | pathlib.Path = None,
        **kwargs,
    ) -> T:
        if name is None:
            name = cls.__name__
        if path is not None:
            path = pathlib.Path(path)
        else:
            path = pathlib.Path()
        lazy_values = {}
        for field in dataclasses.fields(cls):
            # check if the field is in the init
            if field.init:
                lazy_values[field.name] = ZNTRACK_LAZY_VALUE

        lazy_values["name"] = name
        lazy_values["always_changed"] = None  # TODO: read the state from dvc.yaml
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message=".*should not contain '_'*", category=UserWarning
            )
            instance = cls(**lazy_values)
        if remote is not None or rev is not None:
            import dvc.api

            fs = dvc.api.DVCFileSystem(url=remote, rev=rev)
            with fs.open(path / "zntrack.json") as f:
                conf = json.loads(f.read())
                nwd = pathlib.Path(conf[name]["nwd"]["value"])
        else:
            try:
                with open(path / "zntrack.json") as f:
                    conf = json.load(f)
                    nwd = pathlib.Path(conf[name]["nwd"]["value"])
            except FileNotFoundError:
                # from_rev is called before a graph is built
                nwd = NWD_PATH / name
        instance.__dict__["nwd"] = nwd

        # TODO: check if the node is finished or not.
        instance.__dict__["state"] = NodeStatus(
            remote=remote,
            rev=rev,
            state=NodeStatusEnum.RUNNING if running else NodeStatusEnum.FINISHED,
            lazy_evaluation=lazy_evaluation,
            group=Group.from_nwd(instance.nwd),
            path=path,
        ).to_dict()

        instance.__dict__["state"]["plugins"] = get_plugins_from_env(instance)

        with contextlib.suppress(FileNotFoundError):
            # need to update run_count after the state is set
            # TODO: do we want to set the UUID as well?
            # TODO: test that run_count is correct, when using from_rev from another
            #  commit
            with instance.state.fs.open(path / instance.nwd / "node-meta.json") as f:
                content = json.load(f)
                run_count = content.get("run_count", 0)
                run_time = content.get("run_time", 0)
                lockfile = content.get("lockfile", None)
                if node_uuid := content.get("uuid", None):
                    instance._uuid = uuid.UUID(node_uuid)
                instance.__dict__["state"]["run_count"] = run_count
                instance.__dict__["state"]["run_time"] = datetime.timedelta(
                    seconds=run_time
                )
                instance.__dict__["state"]["lockfile"] = lockfile
        if not instance.state.lazy_evaluation:
            for field in dataclasses.fields(cls):
                _ = getattr(instance, field.name)

        instance._external_ = True
        if not running and hasattr(instance, "_post_load_"):
            with contextlib.suppress(NotImplementedError):
                instance._post_load_()

        return instance

    @property
    def state(self) -> NodeStatus:
        if "state" not in self.__dict__:
            self.__dict__["state"] = NodeStatus().to_dict()
            self.__dict__["state"]["plugins"] = get_plugins_from_env(self)

        return NodeStatus(**self.__dict__["state"], node=self)

    @ty_ex.deprecated("loading is handled automatically via lazy evaluation")
    def load(self):
        pass
