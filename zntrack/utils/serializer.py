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
import importlib
import inspect
import logging
from importlib import import_module

import znjson

import zntrack
from zntrack.core.base import Node

log = logging.getLogger(__name__)


class ZnTrackTypeConverter(znjson.ConverterBase):
    """Main Serializer for ZnTrack Nodes, e.g. as dependencies"""

    instance = Node
    representation = "ZnTrackType"

    def _encode(self, obj) -> dict:
        """Convert Node to serializable dict"""
        return {
            "module": obj.module,
            "cls": obj.__class__.__name__,
            "name": obj.node_name,
        }

    def _decode(self, value: dict) -> Node:
        """return serialized Node"""
        module = import_module(value["module"])
        cls = getattr(module, value["cls"])

        return cls.load(name=value["name"])

    def __eq__(self, other):
        """Overwrite check, because checking .zntrack equality"""
        return isinstance(other, Node)


class MethodConverter(znjson.ConverterBase):

    representation = "zn.method"

    def _encode(self, obj):
        """Serialize the object"""
        methods = {
            "module": obj.__class__.__module__,
            "name": obj.__class__.__name__,
            "kwargs": {},
        }

        # If using Jupyter Notebooks

        if zntrack.config.nb_name is not None:
            # if the class is originally imported from main,
            #  it will be copied to the same module path as the
            #  ZnTrack Node source code.
            if methods["module"] == "__main__":
                methods["module"] = obj.znjson_module

        for key in inspect.signature(obj.__class__.__init__).parameters:
            if key == "self":
                continue
            if key in ["args", "kwargs"]:
                log.error(f"Can not convert {key}!")
                continue
            try:
                methods["kwargs"][key] = getattr(obj, key)
            except AttributeError:
                raise AttributeError(
                    f"Could not find {key} in passed method! Please use "
                    "@check_signature from ZnTrack to check that the method signature"
                    " fits the method attributes"
                )

        return methods

    def _decode(self, value: dict):
        """Deserialize the object"""
        module = importlib.import_module(value["module"])
        cls = getattr(module, value["name"])

        return cls(**value["kwargs"])

    def __eq__(self, other) -> bool:
        """Identify if this serializer should be applied"""
        try:
            return other.znjson_zn_method
        except AttributeError:
            return False
