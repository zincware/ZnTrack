"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack parameter
"""
from __future__ import annotations
import logging
import typing

from pytrack.utils.types import NoneType

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from pytrack.utils.type_hints import TypeHintParent


class PyTrackOption:
    def __init__(self, option, default_value, name=None):
        self.option = option
        self.default_value = default_value
        self.name = name

        if option == "result" and default_value is not NoneType:
            raise ValueError(f"Can not pre-initialize result! Found {default_value}")

        self.check_input(default_value)

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance: TypeHintParent, owner):
        log.debug(f"Getting {self.option} / {self.name} for {instance}")
        try:
            return instance.__dict__[self.name]
        except KeyError:
            log.debug('KeyError: returning default value')
            if self.default_value is NoneType:
                return None
            return self.default_value
        except AttributeError:
            log.warning(f'No value found for {self.option} / {self.name} '
                        f'- returning default')
            # This can happen, when instance has not been instantiated, yielding in no
            #  __dict__ attribute. Returning the default value here.
            return self.default_value

    def __set__(self, instance: TypeHintParent, value):
        log.debug(f"Changing {self.option} / {self.name} to {value}")

        if isinstance(value, PyTrackOption):
            log.debug(f'{self.option} / {self.name} is already a PyTrackOption - '
                      f'Skipping updating it!')
            return

        if instance.pytrack.load and self.option != "result":
            raise ValueError(f'Changing {self.option} is currently not allowed!')

        if not instance.pytrack.running and self.option == "result":
            raise ValueError(f'Changing {self.option} is currently not allowed')

        self.check_input(value)

        instance.__dict__[self.name] = value

    def check_input(self, value):
        """Check if the input value can be processed"""
        if isinstance(value, dict):
            log.info(
                f"Used mutable type dict for {self.option}! "
                f"Always overwrite the {self.option} and don't alter it "
                f"otherwise!, It won't work."
            )

        if isinstance(value, list):
            log.info(
                f"Used mutable type list for {self.option}! "
                f"Always overwrite the {self.option} and don't append "
                f"to it! It won't work."
            )


class LazyProperty:
    """Lazy property that takes the attribute name for PyTrackOption definition"""

    def __set_name__(self, owner, name):
        """Descriptor default"""
        self.name = name

    def __get__(self, instance, owner):
        def pass_name(value=NoneType) -> PyTrackOption:
            """
            Parameters
            ----------
            value: any
                Any value to be passed as default to the PyTrackOption

            Returns
            -------
            instantiated PyTrackOption with correct set name and default values

            """
            return PyTrackOption(option=self.name, default_value=value)

        return pass_name


class DVC:
    params = LazyProperty()
    result = LazyProperty()
    deps = LazyProperty()
    outs = LazyProperty()
    metrics_no_cache = LazyProperty()
