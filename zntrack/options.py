import dataclasses
import functools

import znfields
import pandas as pd

from .config import (
    NOT_AVAILABLE,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZNTRACK_OPTION_PLOTS_CONFIG,
    ZNTRACK_PLOTS_AUTOSAVE,
    ZnTrackOptionEnum,
)
from .node import Node

# TODO: default file names like `nwd/metrics.json`, `nwd/node-meta.json`, `nwd/plots.csv` should
# raise an error if passed to `metrics_path` etc.
# TODO: zntrack.outs() and zntrack.outs(cache=False) needs different files!


def _plugin_getter(self: Node, name: str):
    value = PLUGIN_EMPTY_RETRUN_VALUE

    field = self.state.get_field(name)

    for plugin in self.state.plugins.values():
        getter_value = plugin.getter(field)
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
def outs(*, cache: bool = True, independent: bool = False, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    return znfields.field(
        default=NOT_AVAILABLE, getter=_plugin_getter, **kwargs, init=False
    )


@functools.wraps(znfields.field)
def plots(
    *,
    y: str | list[str],
    cache: bool = True,
    independent: bool = False,
    x: str = "step",
    x_label: str | None = None,
    y_label: str | None = None,
    template: str | None = None,
    title: str | None = None,
    autosave: bool = False,
    **kwargs,
):
    """Pandas plot options.

    Parameters
    ----------
    y : str | list[str]
        Column name(s) to plot.
    cache : bool, optional
        Use the DVC cache, by default True.
    independent : bool, optional
        This fields output can be indepented of the
        input to the node. If set tue true, the
        entire Node output will be used for dependencies.
        Can be useful, if the output is e.g.
        a list of indices.
    x : str, optional
        Column name to use for the x-axis, by default "step".
    x_label : str, optional
        Label for the x-axis, by default None.
    y_label : str, optional
        Label for the y-axis, by default None.
    template : str, optional
        Plotly template to use, by default None.
    title : str, optional
        Title of the plot, by default None.
    autosave : bool, optional
        Save the data of this field every time it is being
        updated. Disable for large dataframes.

    """
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PLOTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_PLOTS_AUTOSAVE] = autosave
    plots_config = {}
    for key, value in {
        "x": x,
        "y": y,
        "x_label": x_label,
        "y_label": y_label,
        "template": template,
        "title": title,
    }.items():
        if value is not None:
            plots_config[key] = value
    if plots_config:
        kwargs["metadata"][ZNTRACK_OPTION_PLOTS_CONFIG] = plots_config
    return znfields.field(
        default=NOT_AVAILABLE, getter=_plugin_getter, **kwargs, init=False
    )


@functools.wraps(znfields.field)
def metrics(*, cache: bool = False, independent: bool = False, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.METRICS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    return znfields.field(
        default=NOT_AVAILABLE, getter=_plugin_getter, **kwargs, init=False
    )


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
    return znfields.field(default=default, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
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
    return znfields.field(default=default, getter=_plugin_getter, **kwargs)


@functools.wraps(znfields.field)
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
    return znfields.field(default=default, getter=_plugin_getter, **kwargs)
