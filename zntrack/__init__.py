"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Standard python init file for the main directory
"""

from .core.parameter import DVC
from .core.decorator import Node
from .project import ZnTrackProject
from .interface import DVCInterface
from .utils import config

import logging
import sys

#
__all__ = ["Node", "ZnTrackProject", "DVCInterface", "DVC", "config"]

__version__ = "0.1.2"


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Formatter for advanced logging
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")

channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.DEBUG)
channel.setFormatter(formatter)

logger.addHandler(channel)
