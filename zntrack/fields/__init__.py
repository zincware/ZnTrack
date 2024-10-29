import dataclasses

import pandas as pd
import znfields

from zntrack.config import (
    NOT_AVAILABLE,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZNTRACK_OPTION_PLOTS_CONFIG,
    ZnTrackOptionEnum,
)
from zntrack.fields.deps import deps
from zntrack.fields.params import params
from zntrack.fields.x_path import (
    deps_path,
    metrics_path,
    outs_path,
    params_path,
    plots_path,
)
from zntrack.node import Node
from zntrack.plugins import plugin_getter

# TODO: default file names like `nwd/metrics.json`, `nwd/node-meta.json`, `nwd/plots.csv` should
# raise an error if passed to `metrics_path` etc.
# TODO: zntrack.outs() and zntrack.outs(cache=False) needs different files!


__all__ = ["outs_path", "params_path", "plots_path", "metrics_path", "deps_path", "deps", "params", "plots", "metrics", "outs"]


def _plots_autosave_setter(self: Node, name: str, value: pd.DataFrame):
    value.to_csv((self.nwd / name).with_suffix(".csv"))
    self.__dict__[name] = value





def outs(*, cache: bool = True, independent: bool = False, **kwargs) -> znfields.field:
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )


def plots(
    *,
    y: str | list[str] | None = None,
    cache: bool = True,
    independent: bool = False,
    x: str = "step",
    x_label: str | None = None,
    y_label: str | None = None,
    template: str | None = None,
    title: str | None = None,
    autosave: bool = False,
    **kwargs,
) -> znfields.field:
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
    if y is None:
        y = []
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PLOTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    if autosave:
        kwargs["setter"] = _plots_autosave_setter
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
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )


def metrics(
    *, cache: bool = False, independent: bool = False, **kwargs
) -> znfields.field:
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.METRICS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )
