"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack decorators
"""
import logging

from .py_track import PyTrackParent

log = logging.getLogger(__file__)


class PyTrack:
    def __init__(self, cls=None, jupyter: bool = False, **kwargs):
        self.cls = cls
        self.kwargs = kwargs
        self.jupyter = jupyter
        log.debug(f"decorator_kwargs: {kwargs}")

    def __call__(self, *args, **kwargs):
        log.debug(f"call_args: {args}")
        log.debug(f"call kwargs: {kwargs}")
        if self.cls is None:
            self.cls = args[0]
            return self.apply_decorator(self.cls)

        self.cls = self.apply_decorator(self.cls)
        return self.cls(*args, **kwargs)

    def apply_decorator(self, cls):
        if "run" not in vars(cls):
            raise NotImplementedError("PyTrack class must implement a run method!")
        for name, obj in vars(cls).items():
            if name == "__init__":
                setattr(cls, name, self.init_decorator(obj))
            if name == "__call__":
                setattr(cls, name, self.call_decorator(obj))
            if name == "run":
                setattr(cls, name, self.run_decorator(obj))
        for name, obj in vars(PyTrackParent).items():
            if not name.endswith("__") and name != "run":
                setattr(cls, name, obj)
        print("--------------- \n Got here \n -----------------------")
        return cls

    @staticmethod
    def init_decorator(func):
        def wrapper(cls: PyTrackParent, *args, id_=None, **kwargs):
            PyTrackParent.__init__(cls)
            result = func(cls, *args, **kwargs)
            cls._pytrack_post_init(id_)

            return result

        return wrapper

    @staticmethod
    def call_decorator(f):
        def wrapper(cls: PyTrackParent, *args, force=False, exec_=False, always_changed=False, slurm=False, **kwargs):
            cls._pytrack_pre_call()
            function = f(cls, *args, **kwargs)
            cls._pytrack_post_call(force, exec_, always_changed, slurm)
            return function

        return wrapper

    @staticmethod
    def run_decorator(f):
        def wrapper(cls: PyTrackParent):
            cls._pytrack_pre_run()
            function = f(cls)
            cls._pytrack_post_run()
            return function

        return wrapper
