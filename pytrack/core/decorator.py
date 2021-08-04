"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack decorators
"""

from .py_track import PyTrackParent


def init_decorator(func):
    def wrapper(self: PyTrackParent, *args, id_=None, **kwargs):
        PyTrackParent.__init__(self)
        result = func(self, *args, **kwargs)
        self._pytrack_post_init(id_)
        return result

    return wrapper


def call_decorator(f):
    def wrapper(self: PyTrackParent, *args, force=False, exec_=False, always_changed=False, slurm=False, **kwargs):
        self._pytrack_pre_call()
        function = f(self, *args, **kwargs)
        self._pytrack_post_call(force, exec_, always_changed, slurm)
        return function

    return wrapper


def run_decorator(f):
    def wrapper(self: PyTrackParent):
        self._pytrack_pre_run()
        function = f(self)
        self._pytrack_post_run()
        return function

    return wrapper


def pytrack(cls):
    if "run" not in vars(cls):
        raise NotImplementedError("PyTrack class must implement a run method!")

    for name, obj in vars(cls).items():
        if name == "__init__":
            setattr(cls, name, init_decorator(obj))
        if name == "__call__":
            setattr(cls, name, call_decorator(obj))
        if name == "run":
            setattr(cls, name, run_decorator(obj))
    for name, obj in vars(PyTrackParent).items():
        if not name.endswith("__") and name != "run":
            setattr(cls, name, obj)
    return cls
