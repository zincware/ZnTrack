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
    def __init__(self, option, default_value, name=None):
        self.option = option
        self.default_value = default_value
        self.name = name

        if option == "result" and default_value is not NoneType:
            raise ValueError(f"Can not pre-initialize result! Found {default_value}")

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

            if instance.zntrack.load and self.option != "result":
                raise ValueError(f"Changing {self.option} is currently not allowed!")

            if not instance.zntrack.running and self.option == "result":
                raise ValueError(f"Changing {self.option} is currently not allowed")

            instance.__dict__[self.name] = value


class LazyProperty:
    """Lazy property that takes the attribute name for ZnTrackOption definition"""

    def __set_name__(self, owner, name):
        """Descriptor default"""
        self.name = name

    def __get__(self, instance, owner):
        def pass_name(value=NoneType) -> ZnTrackOption:
            """
            Parameters
            ----------
            value: any
                Any value to be passed as default to the ZnTrackOption

            Returns
            -------
            instantiated ZnTrackOption with correct set name and default values

            """
            return ZnTrackOption(option=self.name, default_value=value)

        return pass_name


class DVC:
    params = LazyProperty()
    result = LazyProperty()

    deps = LazyProperty()

    outs = LazyProperty()
    outs_no_cache = LazyProperty()
    outs_persistent = LazyProperty()

    metrics = LazyProperty()
    metrics_no_cache = LazyProperty()

    plots = LazyProperty()
    plots_no_cache = LazyProperty()
