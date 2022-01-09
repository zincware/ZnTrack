"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: List of functions that are used to serialize and deserialize Python Objects

Notes
-----
    These functions can be used for e.g., small numpy arrays.
    The content will be converted to json serializable data.
    Converting e.g., large numpy arrays can cause major slow downs and is not recommended!
    Please consider using DVC.outs() and save them in a binary file format.

"""
import logging

import znjson

from zntrack.core.base import Node
from zntrack.utils.types import ZnTrackStage

log = logging.getLogger(__name__)


class ZnTrackTypeConverter(znjson.ConverterBase):
    """Main Serializer for ZnTrack Nodes, e.g. as dependencies"""

    instance = Node
    representation = "ZnTrackType"

    def _encode(self, obj) -> dict:
        """Convert Node to serializable dict"""
        return {
            "module": obj.zntrack.module,
            "cls": obj.__class__.__name__,
            "name": obj.zntrack.node_name,
        }

    def _decode(self, value: dict) -> Node:
        """return serialized Node"""
        return ZnTrackStage(**value).load_zntrack_node()

    def __eq__(self, other):
        """Overwrite check, because checking .zntrack equality"""
        return isinstance(other, Node)
