import dataclasses

import yaml

from zntrack.config import PARAMS_FILE_PATH, FieldTypes
from zntrack.fields.base import field
from zntrack.node import Node


def _params_getter(self: "Node", name: str):
    with self.state.fs.open(self.state.path / PARAMS_FILE_PATH) as f:
        return yaml.safe_load(f)[self.name][name]


def params(default=dataclasses.MISSING, **kwargs):
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
        field_type=FieldTypes.PARAMS,
        load_fn=_params_getter,
        suffix=None,
        cache=None,
        independent=None,
        **kwargs,
    )
