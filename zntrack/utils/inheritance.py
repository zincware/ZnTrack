"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Code for using subclasses / inheritance with ZnTrack
"""
import logging

from zntrack import dvc
from zntrack.utils.type_hints import TypeHintParent
import inspect
import abc

log = logging.getLogger(__name__)


class Child:
    # TODO this should probably consist of all dvc/zn types?
    deps: list = []
    outs: list = []


class Base(TypeHintParent):
    """Base class for ZnTrack class inheritance cases

    Attributes
    ----------
    method_name: str
        Name of the method
    method_kwargs: dict
        A dictionary of all the passed args/kwargs gathered from the instantiated method
    methods: dict
        An abstract dictionary that should be overwritten to collect all possible method
        classes

    deps: list, optional
        A list of dependencies from the child class
    outs: list, optional
        A list of outs from the child class

    """

    method_name = dvc.params()
    method_kwargs = dvc.params()
    methods = {}

    deps = dvc.deps()
    outs = dvc.outs()

    # Properties
    _methods = None

    @property
    def method(self):
        """Get the selected method from self.methods with the given arguments"""
        if self._methods is None:
            self._methods = self.methods[self.method_name](**self.method_kwargs)
        return self._methods

    @method.setter
    def method(self, value: Child):
        """Set the method"""
        self.method_name = value.__class__.__name__
        if self.method_name not in self.methods:
            raise KeyError(
                f"Can not find method {self.method_name} in the given methods - "
                f"Check the methods definitions!"
            )
        self.method_kwargs = {}
        for key in inspect.signature(value.__class__.__init__).parameters:
            if key == "self":
                continue
            if key in ["args", "kwargs"]:
                log.error(f"Can not convert {key}!")
                continue
            try:
                self.method_kwargs[key] = getattr(value, key)
            except AttributeError:
                raise AttributeError(
                    f"Could not find {key} in passed method! Please use "
                    f"@check_signature from ZnTrack to check that the method signature"
                    f" fits the method attributes"
                )

        for dependency in value.deps:
            try:
                self.deps.append(dependency)
            except AttributeError:
                self.deps = [dependency]
        for output in value.outs:
            try:
                self.outs.append(output)
            except AttributeError:
                self.outs = [output]

    @abc.abstractmethod
    def run(self):
        """Run method to be called by DVC"""
        pass
