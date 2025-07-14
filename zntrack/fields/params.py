import dataclasses
import typing as t

import yaml

from zntrack.config import PARAMS_FILE_PATH, FieldTypes
from zntrack.fields.base import field
from zntrack.node import Node
from zntrack.utils.filesystem import resolve_state_file_path

_T = t.TypeVar("_T")


def _params_getter(self: "Node", name: str):
    params_path = resolve_state_file_path(
        self.state.fs, self.state.path, PARAMS_FILE_PATH
    )

    with self.state.fs.open(params_path) as f:
        return yaml.safe_load(f)[self.name][name]


# Overloads for type checking
@t.overload
def params(default: _T, **kwargs) -> _T: ...


@t.overload
def params(*, default_factory: t.Callable[[], _T], **kwargs) -> _T: ...


def params(
    default=dataclasses.MISSING, *, default_factory=dataclasses.MISSING, **kwargs
) -> t.Any:
    """ZnTrack parameter field.

    A field to define a parameter for a ZnTrack node.

    Parameters
    ----------
    default : dict|int|str|float|list|None, optional
        Set a default parameter value.

    default_factory : callable, optional
        A callable that returns the default value.
        Should be used instead of `default` if the default value is mutable.

    Examples
    --------

    >>> import zntrack
    >>> class MyNode(zntrack.Node):
    ...     param: int = zntrack.params(default=42)
    ...
    ...     def run(self) -> None: ...
    ...
    >>> a = MyNode()
    >>> a.param
    42
    >>> b = MyNode(param=43)
    >>> b.param
    43

    """
    # TODO: check types, do not allow e.g. connections
    #  or anything that can not be serialized
    return field(
        default=default,
        default_factory=default_factory,
        field_type=FieldTypes.PARAMS,
        load_fn=_params_getter,
        suffix=None,
        cache=kwargs.pop("cache", True),
        independent=kwargs.pop("independent", False),
        **kwargs,
    )
