import dataclasses
import functools

import znfields

_ZNTRACK_OPTION = "zntrack.option"

_ZNTRACK_DEFAULT = object()



@functools.wraps(znfields.field)
def params(default=dataclasses.MISSING, **kwargs):
    # TODO: check types, do not allow e.g. connections or anything that can not be serialized
    return znfields.field(default=default, metadata={_ZNTRACK_OPTION: "params"}, **kwargs)


@functools.wraps(znfields.field)
def deps(default=dataclasses.MISSING, **kwargs):
    return znfields.field(default=default, metadata={_ZNTRACK_OPTION: "deps"}, **kwargs)


@functools.wraps(znfields.field)
def outs(**kwargs):
    return znfields.field(
        default=_ZNTRACK_DEFAULT, metadata={_ZNTRACK_OPTION: "outs"}, **kwargs
    )


@functools.wraps(znfields.field)
def plots(**kwargs):
    return znfields.field(
        default=_ZNTRACK_DEFAULT, metadata={_ZNTRACK_OPTION: "plots"}, **kwargs
    )


@functools.wraps(znfields.field)
def metrics(**kwargs):
    return znfields.field(
        default=_ZNTRACK_DEFAULT, metadata={_ZNTRACK_OPTION: "metrics"}, **kwargs
    )


@functools.wraps(znfields.field)
def params_path(default=dataclasses.MISSING, **kwargs):
    return znfields.field(
        default=default, metadata={_ZNTRACK_OPTION: "params_path"}, **kwargs
    )


@functools.wraps(znfields.field)
def deps_path(default=dataclasses.MISSING, **kwargs):
    return znfields.field(
        default=default, metadata={_ZNTRACK_OPTION: "deps_path"}, **kwargs
    )


@functools.wraps(znfields.field)
def outs_path(default=dataclasses.MISSING, **kwargs):
    return znfields.field(
        default=default, metadata={_ZNTRACK_OPTION: "outs_path"}, **kwargs
    )


@functools.wraps(znfields.field)
def plots_path(default=dataclasses.MISSING, **kwargs):
    return znfields.field(
        default=default, metadata={_ZNTRACK_OPTION: "plots_path"}, **kwargs
    )


@functools.wraps(znfields.field)
def metrics_path(default=dataclasses.MISSING, **kwargs):
    return znfields.field(
        default=default, metadata={_ZNTRACK_OPTION: "metrics_path"}, **kwargs
    )
