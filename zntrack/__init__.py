"""ZnTrack - Create, visualize, run & benchmark DVC pipelines in Python.

GitHub: https://github.com/zincware/ZnTrack
"""
import importlib.metadata

from zntrack import exceptions, tools
from zntrack.core.load import from_rev
from zntrack.core.node import Node
from zntrack.core.nodify import NodeConfig, nodify
from zntrack.fields import Field, FieldGroup, LazyField, dvc, meta, zn
from zntrack.fields.fields import (
    deps,
    deps_path,
    metrics,
    metrics_path,
    outs,
    outs_path,
    params,
    params_path,
    plots,
    plots_path,
)
from zntrack.project import Project
from zntrack.utils import config
from zntrack.utils.node_wd import nwd

__version__ = importlib.metadata.version("zntrack")

__all__ = [
    "Node",
    "dvc",
    "zn",
    "Project",
    "nwd",
    "meta",
    "config",
    "Field",
    "LazyField",
    "FieldGroup",
    "nodify",
    "NodeConfig",
    "tools",
    "exceptions",
    "from_rev",
]

__all__ += [
    "outs",
    "metrics",
    "params",
    "deps",
    "plots",
    "outs_path",
    "metrics_path",
    "params_path",
    "deps_path",
    "plots_path",
]
