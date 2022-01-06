"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Node parameter
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class ZnTrackOption:
    """Descriptor for all DVC options

    This class handles the __get__ and __set__ for the DVC options.
    For most cases this means storing them in the __init__ and keeping track of,
    which Options are used.
    This is required to allow for load=True which updates all ZnTrackOptions,
    based on the computed or otherwise stored values.

    Attributes
    ----------
    option: str
        One of the given options of DVC. The string should also be defined
        inside the dataclass!
    load: bool
        Load this Option  to memory when the stage is called with Stage(load=True)
        This is true for zn.<option> and false for dvc.<option>.

    """

    option = None
    load = False

    def __init__(self, name=None, option=None, load: bool = None):
        """Instantiate a ZnTrackOption Descriptor

        Parameters
        ----------
        name: str
            Required when __set_name__ can not be used, e.g. if the ZnTrackOption
            is defined in the __init__ on not on a class level. It defines
            the name of the descriptor (for self.attr it would be attr).
        option: str
            One of the given options of DVC. The string should also be defined
            inside the dataclass!
        load: bool
            Load this Option  to memory when the stage is called with Stage(load=True)
            This is usually true for zn.<option> and false for dvc.<option>.
            The simplest example is dvc.result() (== zn.outs())
        """
        if option is not None:
            self.option = option

        if load is not None:
            self.load = load
        self.name = name

    @property
    def dvc_parameter(self):
        return self.option.replace("_", "-")

    def __repr__(self):
        return f"{self.__class__}({hex(id(self))}) for <{self.name}>"

    def _get(self, instance, owner):
        """Overwrite this method for custom ZnTrackOption get method"""
        raise NotImplementedError

    def _set(self, instance, value):
        """Overwrite this method for custom ZnTrackOption set method"""
        raise NotImplementedError

    def __set_name__(self, owner, name):
        """Descriptor method to determine the name of the attribute"""
        self.name = name

    def __get__(self, instance, owner):
        """Get the stored value

        typically this reads the stored value from the instance __dict__.
        If no value can be found the configured default value is returned
        """
        log.debug(f"Getting {self.option} / {self.name} for {instance}")
        try:
            return self._get(instance, owner)
        except NotImplementedError:
            try:
                return instance.__dict__[self.name]
            except KeyError:
                ValueError(f"Can not load {self.option} / {self.name} for {instance}!")

    def __set__(self, instance, value):
        """Write the value to the instances __dict__

        Write the given value to the instances __dict__

        Parameters
        ----------
        instance
        value

        """
        if isinstance(instance, tuple):
            log.warning("Converting tuple to list!")
            instance = list(instance)

        log.debug(f"Changing {self.option} / {self.name} to {value}")
        try:
            self._set(instance, value)
        except NotImplementedError:
            instance.__dict__[self.name] = value
