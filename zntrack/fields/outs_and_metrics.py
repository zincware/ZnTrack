import functools
import json

import znfields
import znjson

from zntrack.config import (
    NOT_AVAILABLE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FIELD_SUFFIX,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter
from zntrack.fields.base import field
import dataclasses


def _outs_getter(self: "Node", name: str, suffix: str):
    with self.state.fs.open((self.nwd / name).with_suffix(suffix)) as f:
        return json.load(f, cls=znjson.ZnDecoder)


def _outs_save_func(self: "Node", name: str, suffix: str):
    (self.nwd / name).with_suffix(suffix).write_text(znjson.dumps(getattr(self, name)))


def _metrics_save_func(self: "Node", name: str, suffix: str):
    (self.nwd / name).with_suffix(suffix).write_text(json.dumps(getattr(self, name)))


def outs(*, cache: bool = True, independent: bool = False, **kwargs):
    # kwargs["metadata"] = kwargs.get("metadata", {})
    # kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS
    # kwargs["metadata"][ZNTRACK_CACHE] = cache
    # kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    # kwargs["metadata"][ZNTRACK_FIELD_LOAD] = functools.partial(
    #     base_getter, func=_outs_getter
    # )
    # kwargs["metadata"][ZNTRACK_FIELD_DUMP] = _outs_save_func
    # kwargs["metadata"][ZNTRACK_FIELD_SUFFIX] = ".json"
    # return znfields.field(
    #     default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    # )
    return field(
        default=NOT_AVAILABLE,
        cache=cache,
        independent=independent,
        zntrack_option=ZnTrackOptionEnum.OUTS,
        dump_fn=_outs_save_func,
        suffix=".json",
        load_fn=_outs_getter,
        repr=False,
        init=False,
        **kwargs,
    )


def metrics(
    *, cache: bool = False, independent: bool = False, **kwargs
):
    return field(
        default=NOT_AVAILABLE,
        cache=cache,
        independent=independent,
        zntrack_option=ZnTrackOptionEnum.METRICS,
        dump_fn=_metrics_save_func,
        suffix=".json",
        load_fn=_outs_getter,
        repr=False,
        init=False,
        **kwargs,
    )
