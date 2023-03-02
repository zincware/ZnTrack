"""ZnTrack - Create, visualize, run & benchmark DVC pipelines in Python.

GitHub: https://github.com/zincware/ZnTrack
"""
import importlib.metadata

from zntrack.core.node import Node
from zntrack.fields import dvc, zn

__version__ = importlib.metadata.version("zntrack")

__all__ = ["Node"]
