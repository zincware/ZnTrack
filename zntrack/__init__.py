"""ZnTrack - Create, visualize, run & benchmark DVC pipelines in Python.

GitHub: https://github.com/zincware/ZnTrack
"""
import importlib.metadata

from zntrack.core.node import Node
from zntrack.fields import Field, LazyField, dvc, meta, zn
from zntrack.project import Project
from zntrack.utils import config
from zntrack.utils.node_wd import nwd

__version__ = importlib.metadata.version("zntrack")

__all__ = ["Node", "dvc", "zn", "Project", "nwd", "meta", "config", "Field", "LazyField"]
