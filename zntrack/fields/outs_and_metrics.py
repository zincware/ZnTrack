import dataclasses
import functools
import json

import yaml
import znfields
import znflow
import znflow.handler
import znflow.utils
import znjson

from zntrack import converter
from zntrack.config import (
    NOT_AVAILABLE,
    PARAMS_FILE_PATH,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_GETTER,
    ZNTRACK_FILE_PATH,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZNTRACK_OPTION_PLOTS_CONFIG,
    ZnTrackOptionEnum,
)
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter


def _outs_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".json")) as f:
        self.__dict__[name] = json.load(f, cls=znjson.ZnDecoder)


def outs(*, cache: bool = True, independent: bool = False, **kwargs) -> znfields.field:
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_GETTER] = functools.partial(
        base_getter, func=_outs_getter
    )
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )


def metrics(*, cache: bool = True, independent: bool = False, **kwargs) -> znfields.field:
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.METRICS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_GETTER] = functools.partial(
        base_getter, func=_outs_getter
    )
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )
