import logging
import sys

from zntrack.add import add
from zntrack.apply import apply

from .from_rev import from_rev
from .node import Node
from .options import (
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
from .project import Project
from .utils import nwd

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
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Formatter for advanced logging
formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")

channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.INFO)
channel.setFormatter(formatter)

logger.addHandler(channel)
