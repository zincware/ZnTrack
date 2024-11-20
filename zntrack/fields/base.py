import dataclasses
import functools
import typing as t

import znfields

from zntrack.config import (
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FIELD_SUFFIX,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)

# if t.TYPE_CHECKING:
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter

FN_WITH_SUFFIX = t.Callable[["Node", str, str], t.Any]
FN_WITHOUT_SUFFIX = t.Callable[["Node", str], t.Any]


def field(
    default=dataclasses.MISSING,
    *,
    cache: bool = True,
    independent: bool = False,
    zntrack_option: ZnTrackOptionEnum,
    dump_fn: FN_WITH_SUFFIX | FN_WITHOUT_SUFFIX | None = None,
    suffix: str | None = None,
    load_fn: FN_WITHOUT_SUFFIX | FN_WITH_SUFFIX | None = None,
    **kwargs,
):
    """Create a field with zntrack options."""
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = zntrack_option
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
