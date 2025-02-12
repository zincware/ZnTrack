import dataclasses
import json

import znfields
import znjson

from zntrack import config
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


def params_path(default=dataclasses.MISSING, **kwargs):
    """Define input parameter file path(s).
    
    Parameters
    ----------
    default : str|Path|list[str|Path], optional
        Path to one or multiple parameter files.

    Examples
    --------

    >>> import zntrack
    >>> class MyNode(zntrack.Node):
    ...     params_path: str = zntrack.params_path(default="params.yaml")
    ...
    ...     def run(self) -> None: ...
    ...
    >>> a = MyNode()
    >>> a.params_path
    'params.yaml'
    >>> b = MyNode(params_path="params2.yaml")
    >>> b.params_path
    'params2.yaml'

    """
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PARAMS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = True # TODO: remove?
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def plots_path(
    default=dataclasses.MISSING,
    *,
    cache: bool = True,
    independent: bool = False,
    **kwargs,
):
    """Create a field that handles plots and figure paths.

    Parameters
    ----------
    default : str|Path|list[str|Path], optional
        Path to one or multiple plot files.
        See https://dvc.org/doc/user-guide/experiment-management/visualizing-plots
        for more information.
    cache : bool, optional
        Whether to use the DVC cache for the field.
    independent : bool, optional
        Set to true if the output of this field can be independent of the
        node's inputs. E.g. if a csv file is produced that contains indices
        it might not change if the inputs to the node change.
        In such a case subsequent nodes might not rerun if 
        independent is kept as False.

    Examples
    --------
    >>> import zntrack
    >>> class MyNode(zntrack.Node):
    ...     plots_path: str = zntrack.plots_path(zntrack.nwd / "plots.png")
    ...
    ...     def run(self) -> None: ...
    ...         '''Save a figure to self.plots_path.'''
    """
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PLOTS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def metrics_path(
    default=dataclasses.MISSING,
    *,
    cache: bool | None = None,
    independent: bool = False,
    **kwargs,
):
    if cache is None:
        cache = config.ALWAYS_CACHE
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
