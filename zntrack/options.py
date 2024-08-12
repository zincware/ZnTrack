import dataclasses
import functools

import znfields

_ZNTRACK_OPTION = "zntrack.option"
_ZNTRACK_CACHE = "zntrack.cache"

_ZNTRACK_DEFAULT = object()

# TODO: default file names like `nwd/metrics.json`, `nwd/node-meta.json`, `nwd/plots.csv` should
# raise an error if passed to `metrics_path` etc.
# TODO: zntrack.outs() and zntrack.outs(cache=False) needs different files!


@functools.wraps(znfields.field)
def params(default=dataclasses.MISSING, **kwargs):
    # TODO: check types, do not allow e.g. connections or anything that can not be serialized
    return znfields.field(default=default, metadata={_ZNTRACK_OPTION: "params"}, **kwargs)


@functools.wraps(znfields.field)
def deps(default=dataclasses.MISSING, **kwargs):
    return znfields.field(default=default, metadata={_ZNTRACK_OPTION: "deps"}, **kwargs)


@functools.wraps(znfields.field)
def outs(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][_ZNTRACK_OPTION] = "outs"
    kwargs["metadata"][_ZNTRACK_CACHE] = cache
    return znfields.field(
        default=_ZNTRACK_DEFAULT, **kwargs
    )


@functools.wraps(znfields.field)
def plots(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][_ZNTRACK_OPTION] = "plots"
    kwargs["metadata"][_ZNTRACK_CACHE] = cache
    return znfields.field(
        default=_ZNTRACK_DEFAULT, **kwargs
    )


@functools.wraps(znfields.field)
def metrics(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][_ZNTRACK_OPTION] = "metrics"
    kwargs["metadata"][_ZNTRACK_CACHE] = cache
    return znfields.field(
        default=_ZNTRACK_DEFAULT, **kwargs
    )


@functools.wraps(znfields.field)
def params_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][_ZNTRACK_OPTION] = "params_path"
    kwargs["metadata"][_ZNTRACK_CACHE] = cache
    return znfields.field(
        default=default, **kwargs
    )


@functools.wraps(znfields.field)
def deps_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][_ZNTRACK_OPTION] = "deps_path"
    kwargs["metadata"][_ZNTRACK_CACHE] = cache
    return znfields.field(
        default=default, **kwargs
    )


@functools.wraps(znfields.field)
def outs_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][_ZNTRACK_OPTION] = "outs_path"
    kwargs["metadata"][_ZNTRACK_CACHE] = cache
    return znfields.field(
        default=default, **kwargs
    )


@functools.wraps(znfields.field)
def plots_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][_ZNTRACK_OPTION] = "plots_path"
    kwargs["metadata"][_ZNTRACK_CACHE] = cache
    return znfields.field(
        default=default, **kwargs
    )


@functools.wraps(znfields.field)
def metrics_path(default=dataclasses.MISSING, *, cache: bool = False, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][_ZNTRACK_OPTION] = "metrics_path"
    kwargs["metadata"][_ZNTRACK_CACHE] = cache
    return znfields.field(
        default=default, **kwargs
    )
