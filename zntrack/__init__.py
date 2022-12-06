"""ZnTrack - Create, visualize, run & benchmark DVC pipelines in Python.

GitHub: https://github.com/zincware/ZnTrack
"""
import importlib.metadata
import logging
import sys

import znjson

from zntrack import utils
from zntrack.core.base import Node
from zntrack.core.functions.decorator import NodeConfig, nodify
from zntrack.interface.base import DVCInterface
from zntrack.project.zntrack_project import ZnTrackProject
from zntrack.utils import exceptions, nwd
from zntrack.utils.config import config
from zntrack.utils.serializer import (
    MethodConverter,
    NodeAttributeConverter,
    ZnTrackTypeConverter,
)
from zntrack.zn.dependencies import getdeps

# register converters
znjson.config.register([ZnTrackTypeConverter, MethodConverter, NodeAttributeConverter])

__all__ = [
    Node.__name__,
    ZnTrackProject.__name__,
    DVCInterface.__name__,
    "config",
    nodify.__name__,
    NodeConfig.__name__,
    "getdeps",
    "utils",
    "exceptions",
    "nwd",
]

__version__ = importlib.metadata.version("zntrack")

logger = logging.getLogger(__name__)
logger.setLevel(config.log_level)

# Formatter for advanced logging
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")

channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.DEBUG)
channel.setFormatter(formatter)

logger.addHandler(channel)
