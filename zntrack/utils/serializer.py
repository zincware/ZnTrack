"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: List of functions that are applied to serialize and deserialize Python Objects

Notes
-----
    These functions can be used for e.g., small numpy arrays.
    The content will be converted to json serializable data.
    Converting e.g., large numpy arrays can cause major slow downs and is not recommended!
    Please consider using DVC.outs() and save them in a binary file format.

"""
import logging

import znjson

from zntrack.utils.types import ZnTrackStage, ZnTrackType

log = logging.getLogger(__name__)


class ZnTrackTypeConverter(znjson.ConverterBase):
    """Main Serializer for ZnTrack Nodes, e.g. as dependencies"""

    instance = ZnTrackType
    representation = "ZnTrackType"

    def _encode(self, obj) -> dict:
        """Convert Node to serializable dict"""
        return {
            "module": obj.zntrack.module,
            "cls": obj.__class__.__name__,
            "name": obj.zntrack.stage_name,
        }

    def _decode(self, value: dict):
        """Prepare serialized Node to be converted back"""
        return ZnTrackStage(**value)

    def __eq__(self, other):
        """Overwrite check, because checking .zntrack equality"""
        if hasattr(other, "zntrack"):
            return isinstance(other.zntrack, self.instance)
        return False


class ZnTrackStageConverter(znjson.ConverterBase):
    """

    Required, because when loading the .zntrack file and then serializing it again
    some classes might not be loaded but in the state of ZnTrackStage instead.
    """

    instance = ZnTrackStage
    representation = "ZnTrackStage"

    def _encode(self, obj: ZnTrackStage):
        """Convert ZnTrackStage to dict"""
        return {
            "module": obj.module,
            "cls": obj.cls,
            "name": obj.name,
        }

    def _decode(self, value: dict):
        """Convert dict to ZnTrackStage"""
        return ZnTrackStage(**value)
