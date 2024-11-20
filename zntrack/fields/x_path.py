import dataclasses
import json

import znfields
import znjson

from zntrack.config import (
    NOT_AVAILABLE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FILE_PATH,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_LAZY_VALUE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)

# if t.TYPE_CHECKING:
from zntrack.node import Node
from zntrack.plugins import plugin_getter
from zntrack.utils.misc import TempPathLoader
from zntrack.utils.node_wd import NWDReplaceHandler


def _paths_getter(self: Node, name: str):
    # TODO: if self._external_: try looking into
    # external/self.uuid/...
    # this works for everything except node-meta.json because that
    # defines the uuid
    nwd_handler = NWDReplaceHandler()

    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        return nwd_handler(self.__dict__[name], nwd=self.nwd)
    try:
        with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
            content = json.load(f)[self.name][name]
            content = znjson.loads(json.dumps(content))

            if self.state.tmp_path is not None:
                loader = TempPathLoader()
                loader(content, instance=self)

            content = nwd_handler(content, nwd=self.nwd)

            return content
    except FileNotFoundError:
        return NOT_AVAILABLE


def outs_path(
    default=dataclasses.MISSING,
    *,
    cache: bool = True,
    independent: bool = False,
    **kwargs,
):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def params_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PARAMS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def plots_path(
    default=dataclasses.MISSING,
    *,
    cache: bool = True,
    independent: bool = False,
    **kwargs,
):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PLOTS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def metrics_path(
    default=dataclasses.MISSING,
    *,
    cache: bool = False,
    independent: bool = False,
    **kwargs,
):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.METRICS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def deps_path(default=dataclasses.MISSING, *, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.DEPS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)
