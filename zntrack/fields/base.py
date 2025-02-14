import dataclasses
import functools
import typing as t

import znfields

from zntrack.config import (
    FIELD_TYPE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FIELD_SUFFIX,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    FieldTypes,
)
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter

FN_WITH_SUFFIX = t.Callable[["Node", str, str], t.Any]
FN_WITHOUT_SUFFIX = t.Callable[["Node", str], t.Any]


def field(
    default=dataclasses.MISSING,
    *,
    cache: bool = True,
    independent: bool = False,
    field_type: FieldTypes,
    dump_fn: FN_WITH_SUFFIX | FN_WITHOUT_SUFFIX | None = None,
    suffix: str | None = None,
    load_fn: FN_WITHOUT_SUFFIX | FN_WITH_SUFFIX | None = None,
    **kwargs,
):
    """Create a custom field.

    Arguments
    ---------
    default : t.Any
        Default value of the field.
        For an output field, this should be ``zntrack.NOT_AVAILABLE``
        and should not be set during initialization.
    cache : bool
        Use the DVC cache for the field.
    independent : bool
        If the output of this field can be independent of the input.
    field_type : FieldTypes
        The type of the field.
    dump_fn : FN_WITH_SUFFIX | FN_WITHOUT_SUFFIX
        Function to dump the field.
    suffix : str
        Suffix to append to the field name.
        Can be None if the output is a directory.
    load_fn : FN_WITHOUT_SUFFIX | FN_WITH_SUFFIX
        Function to load the field.
    **kwargs
        Additional arguments to pass to the field.

    Examples
    --------

    >>> import numpy as np
    >>> import zntrack
    ...
    >>>    def _load_fn(self: zntrack.Node, name: str, suffix: str) -> np.ndarray:
    ...        with self.state.fs.open(
    ...            (self.nwd / name).with_suffix(suffix), mode="rb"
    ...        ) as f:
    ...            return np.load(f)
    ...
    >>> def _dump_fn(self: zntrack.Node, name: str, suffix: str) -> None:
    ...     with open((self.nwd / name).with_suffix(suffix), mode="wb") as f:
    ...         np.save(f, getattr(self, name))
    ...
    >>> def numpy_field(*, cache: bool = True, independent: bool = False, **kwargs):
    ...     return field(
                default=zntrack.NOT_AVAILABLE
    ...         cache=cache,
    ...         independent=independent,
    ...         field_type=zntrack.FieldTypes.OUTS,
    ...         dump_fn=_dump_fn,
    ...         suffix=".npy",
    ...         load_fn=_load_fn,
    ...         **kwargs,
    ...     )
    ...
    >>> class MyNode(Node):
    ...     data: np.ndarray = numpy_field()
    ...
    ...     def run(self) -> None:
    ...         self.data = np.arange(9).reshape(3, 3)
    """
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][FIELD_TYPE] = field_type
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    if load_fn is not None:
        kwargs["metadata"][ZNTRACK_FIELD_LOAD] = functools.partial(
            base_getter, func=load_fn
        )
    if dump_fn is not None:
        kwargs["metadata"][ZNTRACK_FIELD_DUMP] = dump_fn
    if suffix is not None:
        kwargs["metadata"][ZNTRACK_FIELD_SUFFIX] = suffix
    return znfields.field(default=default, getter=plugin_getter, **kwargs)
