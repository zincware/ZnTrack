"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: zn.<option>

The following can be used to store e.g. metrics directly without
defining and writing to a file
"""
import logging
import importlib
import inspect

from zntrack.core.parameter import ZnTrackOption

log = logging.getLogger(__name__)


# module class definitions to be used via zn.<option>
# detailed explanations on https://dvc.org/doc/command-reference/run#options
# with the exception that these will be loaded to memory when.
# for direct file references use dvc.<option> instead.


class outs(ZnTrackOption):
    option = "outs"
    load = True


# class plots(ZnTrackOption):
#     option = "plots"
#     load = True


class metrics(ZnTrackOption):
    option = "metrics"
    load = True


class Method(ZnTrackOption):
    """ZnTrack methods passing descriptor

    This descriptor allows to pass a class instance that is not a ZnTrack Node as a
    method that can be used later. It requires that all passed class attributes have
    the same name in the __init__ and via getattr an that they are serializable.

    Example
    --------
    >>> class HelloWorld:
    >>>     def __init__(self, name):
    >>>         self.name = name
    >>> @Node()
    >>> class MyNode
    >>>     my_method = Method()
    >>> MyNode().my_method = HelloWorld(name="Max")

    """

    option = "params"
    load = False

    def _get(self, instance, owner):
        """Custom Get for methods

        Returns
        -------
        object:
            An instance of the passed classed instantiated with the correct arguments.
        """
        methods = instance.__dict__[self.name]
        module = importlib.import_module(methods["module"])
        cls = getattr(module, methods["name"])

        return cls(**methods["kwargs"])

    def _set(self, instance, value: object):
        """Custom Set of Methods

        Save module, name and kwargs from the class state
        """
        methods = {
            "module": value.__class__.__module__,
            "name": value.__class__.__name__,
            "kwargs": {},
        }

        # If using Jupyter Notebooks
        if instance.zntrack.nb_mode:
            # if the class is originally imported from main,
            #  it will be copied to the same module path as the
            #  ZnTrack Node source code.
            if methods["module"] == "__main__":
                methods["module"] = instance.zntrack.module

        for key in inspect.signature(value.__class__.__init__).parameters:
            if key == "self":
                continue
            if key in ["args", "kwargs"]:
                log.error(f"Can not convert {key}!")
                continue
            try:
                methods["kwargs"][key] = getattr(value, key)
            except AttributeError:
                raise AttributeError(
                    f"Could not find {key} in passed method! Please use "
                    f"@check_signature from ZnTrack to check that the method signature"
                    f" fits the method attributes"
                )

        instance.__dict__[self.name] = methods
