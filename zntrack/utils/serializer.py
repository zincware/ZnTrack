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
from pathlib import Path
import numpy as np
from importlib import import_module
from zntrack.utils.types import ZnTrackType, ZnTrackStage

log = logging.getLogger(__name__)


# Serializer
def conv_path_to_dict(value):
    """Convert Path to str"""
    if isinstance(value, Path):
        value = {"Path": value.as_posix()}
    return value


def conv_numpy_to_dict(value):
    """Convert numpy to a list, marked by a dictionary"""
    if isinstance(value, np.ndarray):
        value = {"np": value.tolist()}
    return value


def conv_class_to_dict(value):
    """Serialize class instance

    Parameters
    ----------
    value: decorated Node stage
        Assuming that zntrack stages are written to a file, we use the
        __module and __name__ to later run __module.__name__(load=True)

    Returns
    --------
    dict:
        serialized dictionary containing the class module and name

    """
    if hasattr(value, "zntrack"):
        if isinstance(value.zntrack, ZnTrackType):
            value = {"cls": (value.__module__, value.__class__.__name__)}
    return value


# Deserializer
def conv_dict_to_numpy(value):
    """Convert marked dictionary to a numpy array"""
    if isinstance(value, dict):
        if len(value) == 1 and "np" in value:
            value = np.array(value["np"])
    return value


def conv_dict_to_path(value):
    """Convert marked dictionary to Path"""
    if isinstance(value, dict):
        if len(value) == 1 and "Path" in value:
            value = Path(value["Path"])
    return value


def conv_dict_to_class(value):
    """

    Parameters
    ----------
    value: dict
        Expected a dict of type {'cls': (__module__, __name__)} to run
        from __module__ import __name__ via importlib

    Returns
    -------
    ZnTrackStage(cls=value):
        cls that can be used to load a stage via ZnTrackStage.get()

    """
    if isinstance(value, dict):
        if len(value) == 1 and "cls" in value:
            module = import_module(value["cls"][0])
            value = getattr(module, value["cls"][1])
            value = ZnTrackStage(cls=value)
    return value


def serializer(data):
    """Serialize data so it can be stored in a json file"""
    data = conv_path_to_dict(data)
    data = conv_numpy_to_dict(data)
    data = conv_class_to_dict(data)

    if isinstance(data, list):
        return [serializer(x) for x in data]
    elif isinstance(data, dict):
        return {key: serializer(val) for key, val in data.items()}
    else:
        return data


def deserializer(data):
    """Deserialize data from the json file back to python objects"""
    data = conv_dict_to_numpy(data)
    data = conv_dict_to_path(data)
    data = conv_dict_to_class(data)

    if isinstance(data, list):
        return [deserializer(x) for x in data]
    elif isinstance(data, dict):
        return {key: deserializer(val) for key, val in data.items()}
    else:
        return data
