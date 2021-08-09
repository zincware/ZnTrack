"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack decorators
"""
import logging
import subprocess
from pathlib import Path
import re

from .py_track import PyTrackParent

log = logging.getLogger(__file__)


class PyTrack:
    def __init__(self, cls=None, nb_name: str = None, **kwargs):
        """

        Parameters
        ----------
        cls: object
            Required for use as decorator with @PyTrack
        nb_name: str
            Name of the jupyter notebook e.g. PyTrackNb.ipynb which enables juypter support
        kwargs: No kwars are implemented
        """
        self.cls = cls
        self.kwargs = kwargs
        self.return_with_args = True
        log.debug(f"decorator_kwargs: {kwargs}")

        # jupyter
        if nb_name is not None:
            log.warning(
                "Jupyter support is an experimental feature! Please save your notebook before running this command!\n"
                "Submit issues to https://github.com/zincware/py-track."
            )
            nb_name = Path(nb_name)
        self.nb_name = nb_name
        self.nb_class_path = Path('src')

    def __call__(self, *args, **kwargs):
        """

        Parameters
        ----------
        args: tuple
            The first arg might be the class, if @PyTrack() is used, otherwise args that are passed to the cls
        kwargs: dict
            kwargs that are passed to the cls

        Returns
        -------

        decorated cls

        """
        log.debug(f"call_args: {args}")
        log.debug(f"call kwargs: {kwargs}")

        if self.cls is None:
            self.cls = args[0]
            self.return_with_args = False

        self.apply_decorator()

        if self.nb_name is not None:
            self.jupyter_class_to_file()

        if self.return_with_args:
            return self.cls(*args, **kwargs)
        else:
            return self.cls

    def jupyter_class_to_file(self):
        """Extract the class definition form a ipynb file"""

        subprocess.run(["jupyter", "nbconvert", "--to", "script", self.nb_name])

        reading_class = False

        imports = ""

        class_definition = ""

        with open(Path(self.nb_name).with_suffix(".py"), "r") as f:
            for line in f:
                if line.startswith("import") or line.startswith("from"):
                    imports += line
                if reading_class:
                    if re.match(r'\S', line) and not line.startswith("#") and not line.startswith("class"):
                        reading_class = False
                if reading_class:
                    class_definition += line
                if line.startswith("@PyTrack"):
                    reading_class = True
                    class_definition += "@PyTrack\n"

        src = imports + "\n\n" + class_definition

        src_file = Path(self.nb_class_path, self.cls.__name__).with_suffix(".py")
        self.nb_class_path.mkdir(exist_ok=True, parents=True)
        src_file.write_text(src)

        # Remove converted ipynb file
        self.nb_name.with_suffix(".py").unlink()

    def apply_decorator(self):
        """Apply the decorators to the class methods
        """
        if "run" not in vars(self.cls):
            raise NotImplementedError("PyTrack class must implement a run method!")
        for name, obj in vars(self.cls).items():
            if name == "__init__":
                setattr(self.cls, name, self.init_decorator(obj))
            if name == "__call__":
                setattr(self.cls, name, self.call_decorator(obj))
            if name == "run":
                setattr(self.cls, name, self.run_decorator(obj))
        for name, obj in vars(PyTrackParent).items():
            if not name.endswith("__") and name != "run":
                setattr(self.cls, name, obj)

    def init_decorator(self, func):
        """Decorator to handle the init of the decorated class"""

        def wrapper(cls: PyTrackParent, *args, id_=None, **kwargs):
            PyTrackParent.__init__(cls)
            cls._pytrack_pre_init(id_)
            result = func(cls, *args, **kwargs)
            cls._pytrack_post_init()

            if self.nb_name is not None:
                cls._pytrack__module = f"{self.nb_class_path}.{self.cls.__name__}"

            return result

        return wrapper

    @staticmethod
    def call_decorator(f):
        """Decorator to handle the call of the decorated class"""

        def wrapper(cls: PyTrackParent, *args, force=True, exec_=False, always_changed=False, slurm=False, **kwargs):
            cls._pytrack_pre_call()
            function = f(cls, *args, **kwargs)
            cls._pytrack_post_call(force, exec_, always_changed, slurm)
            return function

        return wrapper

    @staticmethod
    def run_decorator(f):
        """Decorator to handle the run of the decorated class"""

        def wrapper(cls: PyTrackParent):
            cls._pytrack_pre_run()
            function = f(cls)
            cls._pytrack_post_run()
            return function

        return wrapper
