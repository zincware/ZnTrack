"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""

from typing import Callable
from abc import ABC, abstractmethod
import re


class MetaData(ABC):
    """Base class for implementing MetaData decorators

    Attributes
    ----------
    name_of_metric: str
        A string that is unique for this metadata
    """

    name_of_metric: str

    def __init__(self, func: Callable):
        """Get the decorated function

        The MetaData decorator does not take arguments!
        @MetaData() does not work, use @MetaData or implement
        a version that supports both!

        Parameters
        ----------
        func
        """
        self.func: Callable = func
        self.func_name = self.func.__name__

    @abstractmethod
    def __call__(self, cls, *args, **kwargs):
        """Actuall decorator"""
        raise NotImplementedError

    def __get__(self, instance, owner):
        """Converting decorator into descriptor

        tl;dr

        when using the decorator the instance of the decorated class
        is not available and is not passed correctly

        See the following answer for a full explanation why this is required
        https://stackoverflow.com/questions/30104047/how-can-i-decorate-an-instance-method-with-a-decorator-class
        """

        from functools import partial

        return partial(self.__call__, instance)

    def save_metadata(self, cls, value, use_regex: bool = True):
        """Save metadata to the class dict

        Will save the metadata as func_name:metric_name dictionary entry.
        If the func was called multiple times it will increment automatically by
        func_name_<#>:metric_name

        Parameters
        ----------
        cls: the class that has the cls.metadata ZnTrackOption
        value:
            Any value that should be saved
        use_regex: bool, default = True
            Check if the metric already exist and create a new one metric_x.
        """

        try:
            _ = cls.metadata
        except ValueError:
            cls.metadata = {}
        if use_regex:
            pattern = re.compile(rf"{self.func_name}(_[1-9]+)?:{self.name_of_metric}")

            number_already_collected = len(list(filter(pattern.match, cls.metadata)))

            if number_already_collected == 0:
                metadata_name = f"{self.func_name}:{self.name_of_metric}"
            else:
                metadata_name = (
                    f"{self.func_name}_{number_already_collected}:{self.name_of_metric}"
                )
        else:
            metadata_name = f"{self.func_name}:{self.name_of_metric}"

        cls.metadata[metadata_name] = value
