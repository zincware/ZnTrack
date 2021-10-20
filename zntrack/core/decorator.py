"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Node decorators
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
import re
import sys
import typing
import functools

from .zntrack import ZnTrackProperty
from zntrack.utils import config

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from zntrack.utils.type_hints import TypeHintParent


class Node:
    """Decorator for converting a class into a Node stage"""

    def __init__(
        self,
        cls=None,
        nb_name: str = None,
        name: str = None,
        exec_: bool = False,
        **kwargs,
    ):
        """

        Parameters
        ----------
        cls: object
            Required for use as decorator with @Node
        nb_name: str
            Name of the jupyter notebook e.g. ZnTrackNb.ipynb which enables jupyter
            support
        name: str
            A custom name for the DVC stage.
            !There is currently no check in place, that avoids overwriting an existing
            stage!
        exec_: bool
            Set the default value for exec_.
            If true, always run this stage immediately.
        kwargs: No kwargs are implemented
        """
        if cls is not None:
            raise ValueError("Please use `@Node()` instead of `@Node`.")
        self.cls = cls

        if nb_name is None:
            nb_name = config.nb_name

        self.exec_ = exec_

        self.name = name

        self.kwargs = kwargs
        self.return_with_args = True
        log.debug(f"decorator_kwargs: {kwargs}")

        # jupyter
        if nb_name is not None:
            log.warning(
                "Jupyter support is an experimental feature! Please save your "
                "notebook before running this command!\n"
                "Submit issues to https://github.com/zincware/ZnTrack."
            )
            nb_name = Path(nb_name)
        self.nb_name = nb_name
        self.nb_class_path = Path("src")

    def __call__(self, *args, **kwargs):
        """

        Parameters
        ----------
        args: tuple
            The first arg might be the class, if @Node() is used, otherwise args
            that are passed to the cls
        kwargs: dict
            kwargs that are passed to the cls

        Returns
        -------

        decorated cls

        """
        log.debug(f"call_args: {args}")
        log.debug(f"call kwargs: {kwargs}")

        if self.cls is None:
            # This is what gets called with Node()
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
                    if (
                        re.match(r"\S", line)
                        and not line.startswith("#")
                        and not line.startswith("class")
                    ):
                        reading_class = False
                if reading_class or line.startswith("class"):
                    reading_class = True
                    class_definition += line
                if line.startswith("@Node"):
                    reading_class = True
                    class_definition += "@Node()\n"

        src = imports + "\n\n" + class_definition

        src_file = Path(self.nb_class_path, self.cls.__name__).with_suffix(".py")
        self.nb_class_path.mkdir(exist_ok=True, parents=True)

        src_file.write_text(src)

        # Remove converted ipynb file
        self.nb_name.with_suffix(".py").unlink()

    def apply_decorator(self):
        """Apply the decorators to the class methods"""
        if "run" not in vars(self.cls):
            raise NotImplementedError("Node class must implement a run method!")

        if "__call__" not in vars(self.cls):
            setattr(self.cls, "__call__", lambda *args: None)

        if "__init__" not in vars(self.cls):
            setattr(self.cls, "__init__", lambda *args: None)

        for name, obj in vars(self.cls).items():
            if name == "__init__":
                setattr(self.cls, name, self.init_decorator(obj))
            if name == "__call__":
                setattr(self.cls, name, self.call_decorator(obj))
            if name == "run":
                setattr(self.cls, name, self.run_decorator(obj))

    def init_decorator(self, func):
        """Decorator to handle the init of the decorated class"""

        @functools.wraps(func)
        def wrapper(cls: TypeHintParent, *args, id_=None, load: bool = False, **kwargs):
            """Wrapper around the init

            Parameters
            ----------
            cls: TypeHintParent
                a Node decorated class instance
            id_: int
                soon to be depreciated alternative to load
            load: bool
                Load the state and prohibit parameter changes
            args, kwargs:
                parameters to be passed to the cls
            """

            setattr(type(cls), "zntrack", ZnTrackProperty())

            if id_ is not None:
                log.debug("DeprecationWarning: Argument id_ will be removed eventually")
                load = True

            cls.zntrack.load = load
            cls.zntrack.stage_name = self.name

            cls.zntrack.pre_init()
            log.debug(f"Processing {cls.zntrack}")
            result = func(cls, *args, **kwargs)
            cls.zntrack.post_init()

            if self.nb_name is not None:
                cls.zntrack._module = f"{self.nb_class_path}.{self.cls.__name__}"
                cls.zntrack.nb_mode = True

            if cls.zntrack.module == "__main__":
                cls.zntrack._module = Path(sys.argv[0]).stem

            return result

        return wrapper

    def call_decorator(self, func):
        """Decorator to handle the call of the decorated class"""

        @functools.wraps(func)
        def wrapper(
            cls: TypeHintParent,
            *args,
            force=True,
            exec_=self.exec_,
            always_changed=False,
            slurm=False,
            **kwargs,
        ):
            """Wrapper around the call

            Parameters
            ----------
            cls: object
                The class/self argument
            args:
                Args to be passed to the class
            force: bool
                Whether to use dvc with the force argument
            exec_: bool
                Whether to use dvc with the exec argument
            always_changed: bool
                Whether to use dvc with the always_changed argument
            slurm: bool
                Using SLURM with SRUN. (Experimental feature)
            kwargs

            Returns
            -------
            decorated class

            """
            cls.zntrack.pre_call()
            function = func(cls, *args, **kwargs)
            cls.zntrack.post_call(force, exec_, always_changed, slurm)
            return function

        return wrapper

    @staticmethod
    def run_decorator(func):
        """Decorator to handle the run of the decorated class"""

        @functools.wraps(func)
        def wrapper(cls: TypeHintParent):
            """Wrapper around the run method"""
            cls.zntrack.pre_run()
            function = func(cls)
            cls.zntrack.post_run()
            return function

        return wrapper
