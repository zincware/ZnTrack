"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
from functools import wraps
from inspect import signature


def check_signature(func):
    """Check, that the signature keywords match the attribute names

    Valid:
    >>> class HelloWorld:
    >>>    def __init__(self, arg1):
    >>>        self.arg1 = arg1

    Invalid:
    >>> class HelloWorld:
    >>>    def __init__(self, arg):
    >>>        self.arg1 = arg

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        input_signature = [
            key
            for key in signature(func).parameters
            if key not in ["self", "args", "kwargs"]
        ]
        parsed_func = func(self, *args, **kwargs)

        for idx, arg in enumerate(args):
            assert getattr(self, input_signature[idx]) == arg

        for key, val in kwargs.items():
            assert getattr(self, key) == val

        return parsed_func

    return wrapper
