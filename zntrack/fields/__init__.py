from zntrack.fields.base import field
from zntrack.fields.deps import deps
from zntrack.fields.outs_and_metrics import metrics, outs
from zntrack.fields.params import params
from zntrack.fields.plots import plots
from zntrack.fields.x_path import (
    deps_path,
    metrics_path,
    outs_path,
    params_path,
    plots_path,
)

# TODO: default file names like `nwd/metrics.json`,
#  `nwd/node-meta.json`, `nwd/plots.csv` should raise
#  an error if passed to `metrics_path` etc.
# TODO: zntrack.outs() and zntrack.outs(cache=False) needs different files!


__all__ = [
    "outs_path",
    "params_path",
    "plots_path",
    "metrics_path",
    "deps_path",
    "deps",
    "params",
    "plots",
    "metrics",
    "outs",
    "field",
]
