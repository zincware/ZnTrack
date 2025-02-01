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

from zntrack.group import Group
from zntrack.state import NodeStatus
from zntrack.utils.misc import get_plugins_from_env

from .config import NOT_AVAILABLE, ZNTRACK_LAZY_VALUE, NodeStatusEnum

try:
    from typing import dataclass_transform
except ImportError:
    from typing_extensions import dataclass_transform

T = t.TypeVar("T", bound="Node")

log = logging.getLogger(__name__)


def _name_getter(self, attr_name: str) -> str:
    """Retrieve the name of a node based on the current graph context.

    Parameter
    ---------
        attr_name (str): The attribute name to retrieve.

    Returns
    -------
        str: The resolved node name.

    """
    value = self.__dict__.get(attr_name)  # Safer lookup with .get()
    graph = znflow.get_graph()

    # If value exists and the graph is either empty or not inside a group, return it
    if value is not None:
        if graph is znflow.empty_graph or graph.active_group is None:
            return str(value)

    # If no graph is active, return the class name as the default
    if graph is znflow.empty_graph:
        return str(self.__class__.__name__)

    # Compute name based on project-wide node names
    return str(graph.compute_all_node_names()[self.uuid])


@dataclass_transform()
@dataclasses.dataclass(kw_only=True)
class Node(znflow.Node, znfields.Base):
    """A Node."""

    name: str | None = znfields.field(
        default=None, getter=_name_getter
    )  # TODO: add setter and log warning
    always_changed: bool = dataclasses.field(default=False, repr=False)

    _protected_ = znflow.Node._protected_ + ["nwd", "name", "state"]

    def __post_init__(self):
        if self.name is None:
            # automatic node names expects the name to be None when
            # exiting the graph context.
            if not znflow.get_graph() is not znflow.empty_graph:
                self.name = self.__class__.__name__
                if "_" in self.name:
                    log.warning(
                        "Node name should not contain '_'."
                        " This character is used for defining groups."
                    )

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
        **kwargs,
    ) -> T:
        if name is None:
            name = cls.__name__
        lazy_values = {}
        for field in dataclasses.fields(cls):
            # check if the field is in the init
            if field.init:
                lazy_values[field.name] = ZNTRACK_LAZY_VALUE

        lazy_values["name"] = name
        lazy_values["always_changed"] = None  # TODO: read the state from dvc.yaml
        instance = cls(**lazy_values)

        # TODO: check if the node is finished or not.
        instance.__dict__["state"] = NodeStatus(
            remote=remote,
            rev=rev,
            state=NodeStatusEnum.RUNNING if running else NodeStatusEnum.FINISHED,
            lazy_evaluation=lazy_evaluation,
            group=Group.from_nwd(instance.nwd),
        ).to_dict()

        instance.__dict__["state"]["plugins"] = get_plugins_from_env(instance)

        with contextlib.suppress(FileNotFoundError):
            # need to update run_count after the state is set
            # TODO: do we want to set the UUID as well?
            # TODO: test that run_count is correct, when using from_rev from another
            #  commit
            with instance.state.fs.open(instance.nwd / "node-meta.json") as f:
                content = json.load(f)
                run_count = content.get("run_count", 0)
                run_time = content.get("run_time", 0)
                if node_uuid := content.get("uuid", None):
                    instance._uuid = uuid.UUID(node_uuid)
                instance.__dict__["state"]["run_count"] = run_count
                instance.__dict__["state"]["run_time"] = datetime.timedelta(
                    seconds=run_time
                )

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
