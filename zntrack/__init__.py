"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Standard python init file for the main directory
"""

import logging
import sys

import znjson

import zntrack.dvc

from .core.decorator import Node
from .dvc import DVC
from .interface import DVCInterface
from .project import ZnTrackProject
from .utils import config
from .utils.serializer import ZnTrackStageConverter, ZnTrackTypeConverter

# register converters
znjson.config.ACTIVE_CONVERTER = [
    ZnTrackTypeConverter,
    ZnTrackStageConverter,
    znjson.PathlibConverter,
]
try:
    znjson.register(znjson.NumpyConverter)
except ModuleNotFoundError:
    pass

#
__all__ = ["Node", "ZnTrackProject", "DVCInterface", "DVC", "config", "dvc"]

__version__ = "0.2.0"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Formatter for advanced logging
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")

channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.DEBUG)
channel.setFormatter(formatter)

logger.addHandler(channel)
