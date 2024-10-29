import functools
import json

import znfields
import znjson

from zntrack.config import (
    NOT_AVAILABLE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter


def _outs_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".json")) as f:
        self.__dict__[name] = json.load(f, cls=znjson.ZnDecoder)

def _outs_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _metrics_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".json").write_text(json.dumps(getattr(self, name)))



def outs(*, cache: bool = True, independent: bool = False, **kwargs) -> znfields.field:
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = functools.partial(
        base_getter, func=_outs_getter
    )
    kwargs["metadata"][ZNTRACK_FIELD_DUMP] = _outs_save_func
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )


def metrics(
    *, cache: bool = False, independent: bool = False, **kwargs
) -> znfields.field:
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.METRICS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = functools.partial(
        base_getter, func=_outs_getter
    )
    kwargs["metadata"][ZNTRACK_FIELD_DUMP] = _metrics_save_func
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )
