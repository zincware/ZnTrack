import dataclasses
import json
import typing as t
from pathlib import Path

import znfields
import znjson

from zntrack import config
from zntrack.config import (
    FIELD_TYPE,
    NOT_AVAILABLE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FILE_PATH,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_LAZY_VALUE,
    FieldTypes,
)

# if t.TYPE_CHECKING:
from zntrack.node import Node
from zntrack.plugins import plugin_getter
from zntrack.utils.filesystem import resolve_state_file_path
from zntrack.utils.misc import TempPathLoader
from zntrack.utils.node_wd import NWDReplaceHandler

FIELD_PATH_TYPE = t.Union[
    str, Path, t.List[t.Union[str, Path]], dataclasses._MISSING_TYPE
]


def _paths_getter(self: Node, name: str):
    # TODO: if self._external_: try looking into
    # external/self.uuid/...
    # this works for everything except node-meta.json because that
    # defines the uuid
    nwd_handler = NWDReplaceHandler()

    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        return nwd_handler(self.__dict__[name], nwd=self.nwd)
    try:
        zntrack_path = resolve_state_file_path(
            self.state.fs, self.state.path, ZNTRACK_FILE_PATH
        )

        with self.state.fs.open(zntrack_path) as f:
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
    default: FIELD_PATH_TYPE = dataclasses.MISSING,
    *,
    cache: bool = True,
    independent: bool = False,
    **kwargs,
) -> t.Any:
    """Define output file path(s) for a node.

    Parameters
    ----------
    default : str|Path|list[str|Path], optional
        Default path(s) to output files.
    cache : bool, optional
        Whether to use the DVC cache for the field. Default is `True`.
    independent : bool, optional
        Whether the output is independent of the node's inputs. Default is `False`.

    Examples
    --------
    >>> import zntrack
    >>> from pathlib import Path
    >>> class MyNode(zntrack.Node):
    ...     outs_path: Path = zntrack.outs_path(zntrack.nwd / "output.txt")
    ...
    ...     def run(self) -> None: ...
    ...         '''Save output to self.outs_path.'''
    """
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][FIELD_TYPE] = FieldTypes.OUTS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def params_path(default: FIELD_PATH_TYPE = dataclasses.MISSING, **kwargs) -> t.Any:
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
    kwargs["metadata"][FIELD_TYPE] = FieldTypes.PARAMS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = True  # TODO: remove?
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def plots_path(
    default: FIELD_PATH_TYPE = dataclasses.MISSING,
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
    >>> from pathlib import Path
    >>> class MyNode(zntrack.Node):
    ...     plots_path: Path = zntrack.plots_path(zntrack.nwd / "plots.png")
    ...
    ...     def run(self) -> None: ...
    ...         '''Save a figure to self.plots_path.'''
    """
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][FIELD_TYPE] = FieldTypes.PLOTS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def metrics_path(
    default: FIELD_PATH_TYPE = dataclasses.MISSING,
    *,
    cache: bool | None = None,
    independent: bool = False,
    **kwargs,
):
    """Define metrics file path(s) for a node.

    Parameters
    ----------
    default : str|Path|list[str|Path], optional
        Path to one or multiple metrics files.
    cache : bool, optional
        Whether to use the DVC cache for the field. If `None`,
        defaults to `zntrack.config.ALWAYS_CACHE`.
    independent : bool, optional
        Whether the output is independent of the node's inputs. Default is `False`.

    Examples
    --------
    >>> import zntrack
    >>> from pathlib import Path
    >>> class MyNode(zntrack.Node):
    ...     metrics_path: Path = zntrack.metrics_path(zntrack.nwd / "metrics.json")
    ...
    ...     def run(self) -> None: ...
    ...         '''Save metrics to self.metrics_path.'''
    """
    if cache is None:
        cache = config.ALWAYS_CACHE
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][FIELD_TYPE] = FieldTypes.METRICS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)


def deps_path(
    default: FIELD_PATH_TYPE = dataclasses.MISSING, *, cache: bool = True, **kwargs
) -> t.Any:
    """Define dependency file path(s) for a node.

    Parameters
    ----------
    default : str|Path|list[str|Path], optional
        Path to one or multiple dependency files.
    cache : bool, optional
        Whether to use the DVC cache for the field. Default is `True`.

    Examples
    --------
    >>> import zntrack
    >>> class MyNode(zntrack.Node):
    ...     dependencies: str = zntrack.deps_path()
    ...
    ...     def run(self) -> None: ...
    ...
    ... a = MyNode(dependencies=["file1.txt", "file2.txt"])
    """
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][FIELD_TYPE] = FieldTypes.DEPS_PATH
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = _paths_getter
    return znfields.field(default=default, getter=plugin_getter, **kwargs)
