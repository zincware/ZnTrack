import importlib.metadata
import logging
import sys

from zntrack import config
from zntrack.add import add
from zntrack.apply import apply
from zntrack.config import NOT_AVAILABLE, FieldTypes
from zntrack.fields import (
    deps,
    deps_path,
    field,
    metrics,
    metrics_path,
    outs,
    outs_path,
    params,
    params_path,
    plots,
    plots_path,
)
from zntrack.from_rev import from_rev
from zntrack.node import Node
from zntrack.project import Project
from zntrack.utils import nwd

__all__ = [
    "params",
    "deps",
    "outs",
    "plots",
    "metrics",
    "params_path",
    "deps_path",
    "outs_path",
    "plots_path",
    "metrics_path",
    "Node",
    "Project",
    "nwd",
    "from_rev",
    "apply",
    "add",
    "field",
    "FieldTypes",
    "NOT_AVAILABLE",
    "config",
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Formatter for advanced logging
formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")

channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.INFO)
channel.setFormatter(formatter)

logger.addHandler(channel)

__version__ = importlib.metadata.version("zntrack")
