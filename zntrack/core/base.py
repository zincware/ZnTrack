"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
from __future__ import annotations

import json
import logging
import pathlib
import subprocess
import sys

import znjson

from zntrack.descriptor.base import DescriptorIO
from zntrack.utils import config

from .jupyter import jupyter_class_to_file

log = logging.getLogger(__name__)


def get_dvc_arguments(options: dict) -> list:
    """Get the activated options

    Returns
    -------
    list: A list of strings for the subprocess call, e.g.:
        ["--no-commit", "--external"]
    """
    out = []

    for dvc_option, value in options.items():
        if value:
            out.append(f"--{dvc_option.replace('_', '-')}")
        else:
            if dvc_option == "no_exec":
                log.warning(
                    "You will not be able to see the stdout/stderr "
                    "of the process in real time!"
                )
    return out


def handle_deps(value):
    script = []
    if isinstance(value, list) or isinstance(value, tuple):
        for x in value:
            script += handle_deps(x)
    else:
        if isinstance(value, Node):
            for file in value.affected_files:
                script += ["--deps", file]
        else:
            script += ["--deps", value]

    return script


class Node(DescriptorIO):
    is_loaded: bool = False

    _module = None

    @property
    def module(self) -> str:
        """Module from which to import <name>

        Used for from <module> import <name>

        Notes
        -----
        this can be changed when using nb_mode
        """
        if self._module is None:
            if self.__class__.__module__ == "__main__":
                return pathlib.Path(sys.argv[0]).stem
            else:
                return self.__class__.__module__
        return self._module

    @property
    def python_interpreter(self) -> str:
        """Find the most suitable python interpreter

        Try to run subprocess check calls to see, which python interpreter
        should be selected

        Returns
        -------
        interpreter: str
            Name of the python interpreter that works with subprocess calls

        """

        for interpreter in ["python3", "python"]:
            try:
                subprocess.check_call(
                    [interpreter, "--version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                log.debug(f"Using command {interpreter} for dvc!")
                return interpreter

            except subprocess.CalledProcessError:
                log.debug(f"{interpreter} is not working!")
        raise ValueError(
            "Could not find a working python interpreter to work with subprocesses!"
        )

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("Please see <migration tutorial>")

    def save(self):
        self._save_to_file(
            file=pathlib.Path("zntrack.json"), zntrack_type="dvc", key=self.node_name
        )
        self._save_to_file(
            file=pathlib.Path("zntrack.json"), zntrack_type="deps", key=self.node_name
        )
        self._save_to_file(
            file=pathlib.Path("params.yaml"), zntrack_type="params", key=self.node_name
        )
        for option, values in self._descriptor_list.filter(
            zntrack_type="zn", return_with_type=True
        ).items():
            file = pathlib.Path("nodes") / self.node_name / f"{option}.json"
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(json.dumps(values, indent=4, cls=znjson.ZnEncoder))

    def _load(self):
        self._load_from_file(file=pathlib.Path("params.yaml"), key=self.node_name)
        self._load_from_file(file=pathlib.Path("zntrack.json"), key=self.node_name)
        for option in self._descriptor_list.filter(
            zntrack_type="zn", return_with_type=True
        ):
            self._load_from_file(
                file=pathlib.Path("nodes") / self.node_name / f"{option}.json"
            )
        self.is_loaded = True

    def write_graph(
        self,
        silent: bool = False,
        nb_name: str = None,
        no_commit: bool = False,
        external: bool = False,
        always_changed: bool = False,
        no_exec: bool = True,
        force: bool = True,
        no_run_cache: bool = False,
    ):
        """Write the DVC file using run.

        If it already exists it'll tell you that the stage is already persistent and
        has been run before. Otherwise it'll run the stage for you.

        Parameters
        ----------
        silent: bool
            If called with no_exec=False this allows to hide the output from the
            subprocess call.

        Notes
        -----
        If the dependencies for a stage change this function won't necessarily tell you.
        Use 'dvc status' to check, if the stage needs to be rerun.

        """

        self.save()

        if not silent:
            log.warning("--- Writing new DVC file! ---")

        script = ["dvc", "run", "-n", self.node_name]

        script += get_dvc_arguments(
            {
                "no_commit": no_commit,
                "external": external,
                "always_changed": always_changed,
                "no_exec": no_exec,
                "force": force,
                "no_run_cache": no_run_cache,
            }
        )
        if nb_name is None:
            nb_name = config.nb_name

        # Jupyter Notebook
        if nb_name is not None:
            self._module = f"{config.nb_class_path}.{self.__class__.__name__}"

            jupyter_class_to_file(
                silent=silent, nb_name=nb_name, module_name=self.__class__.__name__
            )

            script += [
                "--deps",
                pathlib.Path(*self.module.split(".")).with_suffix(".py").as_posix(),
            ]

        # Handle Parameter
        if len(self._descriptor_list.filter(zntrack_type="params")) > 0:
            script += [
                "--params",
                f"{self.params_file}:{self.node_name}",
            ]
        zn_options_set = set()
        for option in self._descriptor_list.data:
            value = getattr(self, option.name)
            # Handle DVC options
            if option.metadata.zntrack_type == "dvc":
                if isinstance(value, list) or isinstance(value, tuple):
                    for x in value:
                        script += [f"--{option.metadata.dvc_args}", x]
                else:
                    script += [f"--{option.metadata.dvc_args}", value]
            # Handle Zn Options
            elif option.metadata.zntrack_type == "zn":
                zn_options_set.add(
                    (
                        f"--{option.metadata.dvc_args}",
                        pathlib.Path("nodes")
                        / self.node_name
                        / f"{option.metadata.dvc_option}.json",
                    )
                )
            elif option.metadata.zntrack_type == "deps":
                script += handle_deps(value)

        for pair in zn_options_set:
            script += pair

        # Add command to run the script
        cls_name = self.__class__.__name__
        script.append(
            f"""{self.python_interpreter} -c "from {self.module} import {cls_name}; """
            f"""{cls_name}.load(name='{self.node_name}').run_and_save()" """
        )
        log.debug(f"running script: {' '.join([str(x) for x in script])}")

        log.debug(
            "If you are using a jupyter notebook, you may not be able to see the "
            "output in real time!"
        )

        subprocess.check_call(script)

    @classmethod
    def load(cls, name=None) -> Node:
        instance = cls()
        if name not in (None, cls.__name__):
            instance.node_name = name
        instance._load()
        return instance

    def run_and_save(self):
        self.run()
        self.save()

    # @abc.abstractmethod
    def run(self):
        raise NotImplementedError
