"""Provide some additional tools.

This module provides additional tools for ZnTrack.
This includes decorators to time method runtimes.
"""
import functools
from time import time

import numpy as np
import zninit

from zntrack.fields import Field


def timeit(field: str):
    """Decorator to time a function.

    Attributes
    ----------
    field : str
        The field to store the time in.
        The value is stored as {func_name: time} or {func_name: [time1, time2, ...]}
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time()
            result = func(self, *args, **kwargs)
            runtime = time() - start_time

            if field not in [x.name for x in zninit.get_descriptors(Field, self=self)]:
                raise AttributeError(
                    f"Cannot time {func.__name__} because {field} is not an attribute of"
                    f" {self.__class__.__name__}."
                )
            field_data = getattr(self, field, {})
            if not isinstance(field_data, dict):
                # TODO: hotfix, field_data is LazyOption here!
                field_data = {}
            if func.__name__ in field_data:
                value = field_data[func.__name__]
                if not isinstance(value, dict):
                    value = {"values": [value], "mean": value, "std": 0.0}
                value["values"].append(runtime)
                value["mean"] = np.mean(value["values"]).item()
                value["std"] = np.std(value["values"]).item()
                field_data[func.__name__] = value
            else:
                field_data[func.__name__] = runtime
            setattr(self, field, field_data)
            return result

        return wrapper

    return decorator
