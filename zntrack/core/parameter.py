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
import typing

from zntrack.utils.types import NoneType

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from zntrack.utils.type_hints import TypeHintParent


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
        This is usually true for zn.<option> and false for dvc.<option>.
        The simplest example is dvc.result() (== zn.outs())

    """

    option = None
    load = False

    def __init__(self, default_value=NoneType, name=None, option=None):
        """Instantiate a ZnTrackOption Descriptor

        Parameters
        ----------
        default_value:
            Any serializable value which can be used as e.g.
            DVC.params("this is a default").
        name: str
            Required when __set_name__ can not be used, e.g. if the ZnTrackOption
            is defined in the __init__ on not on a class level. It defines
            the name of the descriptor (for self.attr it would be attr).
        """
        if option is not None:
            self.option = option

        if isinstance(default_value, tuple):
            log.warning("Converting tuple to list!")
            default_value = list(default_value)

        self.default_value = default_value
        self.name = name

        if self.load and default_value is not NoneType:
            raise ValueError(
                f"Can not pre-initialize loaded option! Found {default_value}"
            )

    def _get(self, instance: TypeHintParent, owner):
        """Overwrite this method for custom ZnTrackOption get method"""
        raise NotImplementedError

    def _set(self, instance: TypeHintParent, value):
        """Overwrite this method for custom ZnTrackOption set method"""
        raise NotImplementedError

    def __set_name__(self, owner, name):
        """Descriptor method to determine the name of the attribute"""
        self.name = name

    def __get__(self, instance: TypeHintParent, owner):
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
                log.debug("KeyError: returning default value")
                if self.default_value is NoneType:
                    if instance.zntrack.load:
                        raise ValueError(
                            f"Can not load {self.option} / {self.name} for {instance}!"
                            f" Check, if the Node you are trying to access has been "
                            f"run? Check, if you are trying to access some descriptors_from_file e.g."
                            f" in the __init__, before the graph has been executed. You"
                            f" could consider adding `exec_=True` to your class to "
                            f"circumvent this behaviour."
                        )
                    return None
                return self.default_value
            except AttributeError:
                log.warning(
                    f"No value found for {self.option} / {self.name} "
                    f"- returning default"
                )
                # This can happen, when instance has not been instantiated, yielding in
                # no __dict__ attribute. Returning the default value here.
                return self.default_value

    def __set__(self, instance: TypeHintParent, value):
        """Write the value to the instances __dict__

        typically write the given value to the instances __dict__

        Parameters
        ----------
        instance
        value

        Returns
        -------

        """
        if isinstance(instance, tuple):
            log.warning("Converting tuple to list!")
            instance = list(instance)

        log.debug(f"Changing {self.option} / {self.name} to {value}")
        try:
            self._set(instance, value)
        except NotImplementedError:
            if isinstance(value, ZnTrackOption):
                log.debug(
                    f"{self.option} / {self.name} is already a ZnTrackOption - "
                    f"Skipping updating it!"
                )
                return

            if instance.zntrack.load and not self.load:
                raise ValueError(f"Changing {self.option} is currently not allowed!")

            if not instance.zntrack.running and self.load:
                raise ValueError(f"Changing {self.option} is currently not allowed")

            instance.__dict__[self.name] = value
