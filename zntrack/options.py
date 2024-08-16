import dataclasses
import functools
import json

import yaml
import znfields
import znflow
import znjson

from .config import (
    PARAMS_FILE_PATH,
    ZNTRACK_CACHE,
    ZNTRACK_DEFAULT,
    ZNTRACK_FILE_PATH,
    ZNTRACK_LAZY_VALUE,
    ZNTRACK_OPTION,
    ZNTRACK_SAVE_FUNC,
    NodeStatusEnum,
)
from .converter import ConnectionConverter, NodeConverter
from .node import Node

# TODO: default file names like `nwd/metrics.json`, `nwd/node-meta.json`, `nwd/plots.csv` should
# raise an error if passed to `metrics_path` etc.
# TODO: zntrack.outs() and zntrack.outs(cache=False) needs different files!


def _params_getter(self: Node, name: str):
    if name in self.__dict__:
        if self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
            return self.__dict__[name]
    with self.state.fs.open(PARAMS_FILE_PATH) as f:
        self.__dict__[name] = yaml.safe_load(f)[self.name][name]
        return getattr(self, name)


def _paths_getter(self: Node, name: str):
    if name in self.__dict__:
        if self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
            return self.__dict__[name]
    with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        # TODO: replace nwd
        content = znjson.loads(json.dumps(content))
        self.__dict__[name] = content
        return getattr(self, name)


def _outs_getter(self: Node, name: str):
    if name in self.__dict__:
        if self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
            return self.__dict__[name]
    
    if self.state.state == NodeStatusEnum.RUNNING:
        return ZNTRACK_LAZY_VALUE
    with self.state.fs.open((self.nwd / name).with_suffix(".json")) as f:
        self.__dict__[name] = json.load(f)
    return getattr(self, name)


def _outs_save_func(self: Node, name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _metrics_save_func(self: Node, name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _plots_save_func(self: Node, name: str):
    (self.nwd / name).with_suffix(".csv").write_text(getattr(self, name).to_csv())


def _deps_getter(self: Node, name: str):
    if name in self.__dict__:
        if self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
            return self.__dict__[name]

    with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        # TODO: when loading deps, make sure they are loaded from the correct revision!
        content = znjson.loads(
            json.dumps(content),
            cls=znjson.ZnDecoder.from_converters(
                [NodeConverter, ConnectionConverter], add_default=True
            ),
        )
        # if any connection in conent, resolve it
        # TODO: use znflow.utils.IteratorHelper
        if isinstance(content, list):
            content = [
                c.result if isinstance(c, znflow.Connection) else c for c in content
            ]
        if isinstance(content, znflow.Connection):
            content = content.result
        self.__dict__[name] = content
    return getattr(self, name)


@functools.wraps(znfields.field)
def params(default=dataclasses.MISSING, **kwargs):
    # TODO: check types, do not allow e.g. connections or anything that can not be serialized
    return znfields.field(
        default=default,
        metadata={ZNTRACK_OPTION: "params"},
        getter=_params_getter,
        **kwargs,
    )


@functools.wraps(znfields.field)
def deps(default=dataclasses.MISSING, **kwargs):
    return znfields.field(
        default=default, metadata={ZNTRACK_OPTION: "deps"}, getter=_deps_getter, **kwargs
    )


@functools.wraps(znfields.field)
def outs(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = "outs"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_SAVE_FUNC] = _outs_save_func
    return znfields.field(default=ZNTRACK_DEFAULT, getter=_outs_getter, **kwargs)


@functools.wraps(znfields.field)
def plots(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = "plots"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_SAVE_FUNC] = _plots_save_func
    return znfields.field(default=ZNTRACK_DEFAULT, getter=_outs_getter, **kwargs)


@functools.wraps(znfields.field)
def metrics(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = "metrics"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_SAVE_FUNC] = _metrics_save_func
    return znfields.field(default=ZNTRACK_DEFAULT, getter=_outs_getter, **kwargs)


@functools.wraps(znfields.field)
def params_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = "params_path"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_paths_getter, **kwargs)


@functools.wraps(znfields.field)
def deps_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = "deps_path"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_paths_getter, **kwargs)


@functools.wraps(znfields.field)
def outs_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = "outs_path"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_paths_getter, **kwargs)


@functools.wraps(znfields.field)
def plots_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = "plots_path"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_paths_getter, **kwargs)


@functools.wraps(znfields.field)
def metrics_path(default=dataclasses.MISSING, *, cache: bool = False, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = "metrics_path"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=default, getter=_paths_getter, **kwargs)
