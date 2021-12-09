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
from zntrack.core.data_classes import DVCOptions
from zntrack.utils import config
from zntrack.metadata import MetaData

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
        no_exec: bool = True,
        silent: bool = False,
        external: bool = False,
        no_commit: bool = False,
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
        no_exec: bool
            Set the default value for no_exec.
            If true, always run this stage immediately.
        silent: bool
            If called with no_exec=False this allows to hide the output from the
            subprocess call.
        external: bool, default = False
            Add the `--external` argument to the dvc run command, that indicates that
            outs or deps can be located outside of the repository
        no_commit: bool, default=False
            Add the `--no-commit` argument to the dvc run command
        kwargs: No kwargs are implemented
        """
        if cls is not None:
            raise ValueError("Please use `@Node()` instead of `@Node`.")
        self.cls = cls

        if "exec_" in kwargs:
            self.no_exec = not kwargs.get("exec_")
            log.warning("DeprecationWarning: Please use no_exec instead of exec_")
        else:
            self.no_exec = no_exec
        self.external = external
        self.no_commit = no_commit
        self.silent = silent

        self.name = name

        self.kwargs = kwargs
        self.return_with_args = True
        log.debug(f"decorator_kwargs: {kwargs}")

        self.has_metadata = False

        if nb_name is None:
            nb_name = config.nb_name

        # jupyter
        if nb_name is not None:
            if not self.silent:
                log.warning(
                    "Jupyter support is an experimental feature! Please save your "
                    "notebook before running this command!\n"
                    "Submit issues to https://github.com/zincware/ZnTrack."
                )
            nb_name = Path(nb_name)
        self.nb_name = nb_name

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

        self.check_for_metadata_decorators()

        self.apply_decorator()

        if self.nb_name is not None:
            self.jupyter_class_to_file()

        if self.return_with_args:
            return self.cls(*args, **kwargs)
        else:
            return self.cls

    def check_for_metadata_decorators(self):
        """Check if the decorated class has any metadata collection

        Go through all functions of the decorated class and check if one of them
        is an instance of the MetaData decorator. If this is the case we need
        to add the metadata zn.metrics to the class!
        """

        for key, val in vars(self.cls).items():
            try:
                if isinstance(val, MetaData):
                    self.has_metadata = True
                    log.debug(f"{key} is decorated with {val.name_of_metric}!")
            except AttributeError:
                pass

    def jupyter_class_to_file(self):
        """Extract the class definition form a ipynb file"""

        if self.silent:
            _ = subprocess.run(
                ["jupyter", "nbconvert", "--to", "script", self.nb_name],
                capture_output=True,
            )
        else:
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

        src_file = Path(config.nb_class_path, self.cls.__name__).with_suffix(".py")
        config.nb_class_path.mkdir(exist_ok=True, parents=True)

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
        def wrapper(
            cls: TypeHintParent,
            *args,
            id_=None,
            load: bool = False,
            name: str = self.name,
            **kwargs,
        ):
            """Wrapper around the init

            Parameters
            ----------
            cls: TypeHintParent
                a Node decorated class instance
            id_: int
                soon to be depreciated alternative to load
            name: str
                Overwrite for the default name based on class.__name__
            load: bool
                Load the state and prohibit parameter changes
            args, kwargs:
                parameters to be passed to the cls
            """

            setattr(type(cls), "zntrack", ZnTrackProperty())

            if id_ is not None:
                log.debug("DeprecationWarning: Argument id_ will be removed eventually")
                load = True

            cls.zntrack.pre_init(
                name=name, load=load, has_metadata=self.has_metadata,
            )
            log.debug(f"Processing {cls.zntrack}")
            parsed_function = func(cls, *args, **kwargs)
            cls.zntrack.post_init()

            if self.nb_name is not None:
                cls.zntrack._module = f"{config.nb_class_path}.{self.cls.__name__}"
                cls.zntrack.nb_mode = True

            if cls.zntrack.module == "__main__":
                cls.zntrack._module = Path(sys.argv[0]).stem

            return parsed_function

        return wrapper

    def call_decorator(self, func):
        """Decorator to handle the call of the decorated class"""

        @functools.wraps(func)
        def wrapper(
            cls: TypeHintParent,
            *args,
            force=True,
            no_exec=self.no_exec,
            always_changed=False,
            slurm=False,
            silent=self.silent,
            external=self.external,
            no_commit=self.no_commit,
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
            no_exec: bool, default=True
                Whether to use dvc with the no_exec argument
            always_changed: bool
                Whether to use dvc with the always_changed argument
            slurm: bool
                Using SLURM with SRUN. (Experimental feature)
            silent: bool
                If called with no_exec=False this allows to hide the output from the
                subprocess call.
            external: bool, default = False
                Add the `--external` argument to the dvc run command, that indicates
                that outs or deps can be located outside of the repository
            no_commit: bool, default=False
                Add the `no-commit` dvc run argument.
            kwargs

            Returns
            -------
            decorated class

            """

            if "exec_" in kwargs:
                no_exec = not kwargs.pop("exec_")
                log.warning("DeprecationWarning: Please use no_exec instead of exec_")

            dvc_options = DVCOptions(
                force=force,
                no_exec=no_exec,
                always_changed=always_changed,
                external=external,
                no_commit=no_commit,
            )

            cls.zntrack.pre_call()
            parsed_function = func(cls, *args, **kwargs)
            cls.zntrack.post_call(
                dvc_options=dvc_options, slurm=slurm, silent=silent,
            )
            return parsed_function

        return wrapper

    @staticmethod
    def run_decorator(func):
        """Decorator to handle the run of the decorated class"""

        @functools.wraps(func)
        def wrapper(cls: TypeHintParent):
            """Wrapper around the run method"""
            cls.zntrack.pre_run()
            parsed_function = func(cls)
            cls.zntrack.post_run()
            return parsed_function

        return wrapper
