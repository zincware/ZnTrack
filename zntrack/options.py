import dataclasses
import functools

import znfields

from .config import (
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
    ZNTRACK_DEFAULT,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from .node import Node

# TODO: default file names like `nwd/metrics.json`, `nwd/node-meta.json`, `nwd/plots.csv` should
# raise an error if passed to `metrics_path` etc.
# TODO: zntrack.outs() and zntrack.outs(cache=False) needs different files!


def _plugin_getter(self: Node, name: str):
    value = PLUGIN_EMPTY_RETRUN_VALUE
    fields = dataclasses.fields(self)
    field = [_field for _field in fields if _field.name == name][0]

    for plugin in self.state.plugins:
        getter_value = plugin.getter(self, field)
        if getter_value is not PLUGIN_EMPTY_RETRUN_VALUE:
            if value is not PLUGIN_EMPTY_RETRUN_VALUE:
                raise ValueError(
                    f"Multiple plugins return a value for {name}: {value} and {getter_value}"
                )
            value = getter_value
    return value


@functools.wraps(znfields.field)
def params(default=dataclasses.MISSING, **kwargs):
    # TODO: check types, do not allow e.g. connections or anything that can not be serialized
    return znfields.field(
        default=default,
        metadata={ZNTRACK_OPTION: ZnTrackOptionEnum.PARAMS},
        getter=_plugin_getter,
        **kwargs,
    )


@functools.wraps(znfields.field)
def deps(default=dataclasses.MISSING, **kwargs):
    return znfields.field(
        default=default,
        metadata={ZNTRACK_OPTION: ZnTrackOptionEnum.DEPS},
        getter=_plugin_getter,
        **kwargs,
    )


@functools.wraps(znfields.field)
def outs(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=ZNTRACK_DEFAULT, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
def plots(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PLOTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=ZNTRACK_DEFAULT, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
def metrics(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.METRICS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=ZNTRACK_DEFAULT, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
def params_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PARAMS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
def deps_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.DEPS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
def outs_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
def plots_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PLOTS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
def metrics_path(default=dataclasses.MISSING, *, cache: bool = False, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.METRICS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_plugin_getter, **kwargs)
