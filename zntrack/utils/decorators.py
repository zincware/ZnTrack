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
