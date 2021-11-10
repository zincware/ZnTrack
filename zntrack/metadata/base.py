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


class MetaData(ABC):
    name_of_metric: str

    def __init__(self, func: Callable):
        self.func: Callable = func
        self.func_name = self.func.__name__

    @abstractmethod
    def __call__(self, cls, *args, **kwargs):
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

    def save_metadata(self, cls, value):
        try:
            cls.metadata.update({f"{self.func_name}:{self.name_of_metric}": value})
        except ValueError:
            cls.metadata = {f"{self.func_name}:{self.name_of_metric}": value}
