import functools

import pandas as pd
import znfields

from zntrack.config import (
    NOT_AVAILABLE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZNTRACK_OPTION_PLOTS_CONFIG,
    ZnTrackOptionEnum,
)
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter


def _plots_save_func(self: "Node", name: str):
    content = getattr(self, name)
    if not isinstance(content, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(content)}")
    content.to_csv((self.nwd / name).with_suffix(".csv"))


def _plots_autosave_setter(self: Node, name: str, value: pd.DataFrame):
    value.to_csv((self.nwd / name).with_suffix(".csv"))
    self.__dict__[name] = value


def _plots_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".csv")) as f:
        self.__dict__[name] = pd.read_csv(f, index_col=0)


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
    else:
        kwargs["metadata"][ZNTRACK_FIELD_DUMP] = _plots_save_func
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

    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = functools.partial(
        base_getter, func=_plots_getter
    )
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )
