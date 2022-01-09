"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
from __future__ import annotations

import abc
import dataclasses
import json
import logging
import pathlib
import re
import subprocess
import sys
import typing

import yaml
import znjson

from zntrack.core.parameter import ZnTrackOption
from zntrack.utils import config

log = logging.getLogger(__name__)


def handle_single_dvc_option(option: ZnTrackOption, value) -> [str, str]:
    if isinstance(value, Node):
        if option.option == "deps":
            for file in value.zntrack.affected_files:
                return ["--deps", file]
        else:
            raise NotImplementedError(f"Can not convert {value} to {option.option}")
    elif isinstance(value, str):
        file = pathlib.Path(value).as_posix()
        return [f"--{option.dvc_parameter}", file]
    elif isinstance(value, pathlib.Path):
        return [f"--{option.dvc_parameter}", value.as_posix()]
    else:
        raise NotImplementedError(f"Type {type(value)} is currently not supported")


def jupyter_class_to_file(silent, nb_name, module_name):
    """Extract the class definition form a ipynb file"""

    nb_name = pathlib.Path(nb_name)

    if silent:
        _ = subprocess.run(
            ["jupyter", "nbconvert", "--to", "script", nb_name],
            capture_output=True,
        )
    else:
        subprocess.run(["jupyter", "nbconvert", "--to", "script", nb_name])

    reading_class = False

    imports = ""

    class_definition = ""

    with open(pathlib.Path(nb_name).with_suffix(".py"), "r") as f:
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

    src_file = pathlib.Path(config.nb_class_path, module_name).with_suffix(".py")
    config.nb_class_path.mkdir(exist_ok=True, parents=True)

    src_file.write_text(src)

    # Remove converted ipynb file
    nb_name.with_suffix(".py").unlink()


@dataclasses.dataclass(frozen=False, order=True, init=True)
class DVCOptions:
    """Extension to the DVCParams
    DVCParams handles e.g. I/O whilst DVCOptions handles all other parameters,
    such as the name, exec, force, commit, external, ...
    See Also
    --------
    https://dvc.org/doc/command-reference/run
    """

    no_commit: bool = False
    external: bool = False
    always_changed: bool = False
    no_exec: bool = False
    force: bool = False
    no_run_cache: bool = False

    @property
    def dvc_arguments(self) -> list:
        """Get the activated options
        Returns
        -------
        list: A list of strings for the subprocess call
            ["--no-commit", "--external"]
        """
        out = []

        for dvc_option in self.__dataclass_fields__:
            value = getattr(self, dvc_option)
            if isinstance(value, bool):
                if value:
                    out.append(f"--{dvc_option.replace('_', '-')}")
                else:
                    if dvc_option == "no_exec":
                        log.warning(
                            "You will not be able to see the stdout/stderr "
                            "of the process in real time!"
                        )
            else:
                raise NotImplementedError("Currently only boolean values are supported")

        return out


class ZnTrack:
    params_file = pathlib.Path("params.yaml")
    zntrack_file = pathlib.Path("zntrack.json")

    def __init__(
        self,
        parent,
        dvc_options: DVCOptions = DVCOptions(),
        name=None,
        nb_name: str = config.nb_name,
        has_metadata: bool = False,
    ):

        self.dvc_options = dvc_options

        self.nb_name = nb_name
        self.has_metadata = has_metadata

        self._stage_name = name
        self._module = None
        self.parent = parent
        self.option_tracker = ZnTrackOptionTracker()

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

    @property
    def name(self) -> str:
        """required for the dvc run command

        Used in
        .. code-block::

            self.python_interpreter -c f"from {self.module} import {self.name};"
                f'{self.name}(load=True).run()"'

        Returns
        -------
        str: Name of this class

        """
        # TODO rename stage_name to name and remove name/rename it
        return self.parent.__class__.__name__

    @property
    def module(self) -> str:
        """Module from which to import <name>

        Used for from <module> import <name>

        Notes
        -----
        this can be changed when using nb_mode
        """
        if self._module is None:
            if self.parent.__class__.__module__ == "__main__":
                self._module = pathlib.Path(sys.argv[0]).stem
            else:
                self._module = self.parent.__class__.__module__
        return self._module

    @property
    def stage_name(self) -> str:
        """Get the stage name"""
        if self._stage_name is None:
            return self.name
        return self._stage_name

    @property
    def zn_outs_path(self) -> pathlib.Path:
        return pathlib.Path("nodes") / self.stage_name

    @stage_name.setter
    def stage_name(self, value):
        """Set the stage name"""
        self._stage_name = value

    @property
    def affected_files(self) -> typing.Set[pathlib.Path]:
        files = []
        for option in self.option_tracker.dvc_options:
            value = getattr(self.parent, option.name)
            # TODO allow for arbitrary recursion depth, maybe log a warning if depth > 10
            if isinstance(value, Node):
                files += list(value.zntrack.affected_files)
            else:
                if isinstance(value, list) or isinstance(value, tuple):
                    files += [pathlib.Path(x) for x in value]
                else:
                    files.append(pathlib.Path(value))
        # Handle Zn Options
        for value in self.option_tracker.zn_options:
            files.append(self.zn_outs_path / f"{value.option}.json")
        return set(files)

    def update_option_tracker(self):
        for option in vars(type(self.parent)).values():
            if isinstance(option, ZnTrackOption):
                if option.option == "params":
                    if option not in self.option_tracker.params:
                        self.option_tracker.params.append(option)
                elif option.load:
                    if option not in self.option_tracker.zn_options:
                        self.option_tracker.zn_options.append(option)
                else:
                    if option not in self.option_tracker.dvc_options:
                        self.option_tracker.dvc_options.append(option)

    def load(self):
        # 0. Find all ZnTrackOptions and update the option_tracker
        # 1. Load params from yaml file
        # 2. Load dvc options from zntrack file
        # 3. Load zn options from /nodes/<node_name>/...
        self.update_option_tracker()
        self._load_params()
        self._load_dvc_options()
        self._load_zn_options()

    def _load_params(self):
        try:
            with self.params_file.open("r") as f:
                full_params_file = yaml.safe_load(f)
        except FileNotFoundError:
            log.debug(f"No Parameter file ({self.params_file}) found!")
            return
        try:
            self.parent.__dict__.update(full_params_file[self.stage_name])
        except KeyError:
            log.debug(f"No Parameters for {self.stage_name} found in {self.params_file}")

    def _load_dvc_options(self):
        try:
            zntrack_file = json.loads(self.zntrack_file.read_text())
        except FileNotFoundError:
            log.debug(f"Could not load params from {self.zntrack_file}!")
            return
        try:
            # The problem here is, that I can not / don't want to load all Nodes but only
            # the ones, that are in [self.stage_name], so we only deserialize them
            data = json.loads(
                json.dumps(zntrack_file[self.stage_name]), cls=znjson.ZnDecoder
            )
            self.parent.__dict__.update(data)
        except KeyError:
            log.debug(f"No DVC Options for {self.stage_name} found in {self.params_file}")

    def _load_zn_options(self):
        # TODO this is not save an will read all json files in that directory!
        self.zn_outs_path.mkdir(parents=True, exist_ok=True)
        options = {}

        for file in self.zn_outs_path.glob("*.json"):
            options.update(json.loads(file.read_text(), cls=znjson.ZnDecoder))

        self.parent.__dict__.update(options)

    def save(self):
        # 0. Find all ZnTrackOptions and update the option_tracker
        # 1. Save params to yaml file
        # 2. Save dvc options to zntrack file
        # 3. Save zn.<option> to /nodes/<node_name>/...
        self.update_option_tracker()
        self._save_params()
        self._save_dvc_options()
        self._save_zn_options()

    def _save_params(self):
        params = {}
        for param in self.option_tracker.params:
            params[param.name] = getattr(self.parent, param.name)

        try:
            with self.params_file.open("r") as f:
                full_params_file = yaml.safe_load(f)
        except FileNotFoundError:
            full_params_file = {}
        full_params_file[self.stage_name] = params

        with self.params_file.open("w") as f:
            yaml.safe_dump(full_params_file, f, indent=4)

    def _save_dvc_options(self):
        options = {}
        for value in self.option_tracker.dvc_options:
            options[value.name] = getattr(self.parent, value.name)

        try:
            zntrack_file = json.loads(self.zntrack_file.read_text(), cls=znjson.ZnDecoder)
        except FileNotFoundError:
            log.debug(f"Could not load params from {self.zntrack_file}!")
            zntrack_file = {}

        zntrack_file[self.stage_name] = options

        self.zntrack_file.write_text(
            json.dumps(zntrack_file, indent=4, cls=znjson.ZnEncoder)
        )

    def _save_zn_options(self):
        options = {}
        for value in self.option_tracker.zn_options:
            try:
                options[value.option].update(
                    {value.name: getattr(self.parent, value.name)}
                )
            except KeyError:
                options[value.option] = {value.name: getattr(self.parent, value.name)}

        # need to create the paths even if no zn is found, because it is required for
        # dvc to write the .gitignore when they apply in the run method
        self.zn_outs_path.mkdir(parents=True, exist_ok=True)
        for option, values in options.items():
            file = self.zn_outs_path / f"{option}.json"
            file.write_text(json.dumps(values, indent=4, cls=znjson.ZnEncoder))

        return options

    def write_dvc(
        self,
        silent: bool = False,
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
        if not silent:
            log.warning("--- Writing new DVC file! ---")

        script = ["dvc", "run", "-n", self.stage_name]

        script += self.dvc_options.dvc_arguments

        # Jupyter Notebook
        if self.nb_name is not None:
            self._module = f"{config.nb_class_path}.{self.parent.__class__.__name__}"

            jupyter_class_to_file(
                silent=silent, nb_name=self.nb_name, module_name=self.module
            )

            script += [
                "--deps",
                pathlib.Path(*self.module.split(".")).with_suffix(".py").as_posix(),
            ]

        # Handle Parameter
        if len(self.option_tracker.params) > 0:
            script += [
                "--params",
                f"{self.params_file}:{self.stage_name}",
            ]
        # Handle DVC options
        for option in self.option_tracker.dvc_options:
            value = getattr(self.parent, option.name)
            if isinstance(value, list) or isinstance(value, tuple):
                for single_value in value:
                    script += handle_single_dvc_option(option, single_value)
            else:
                script += handle_single_dvc_option(option, value)
        # Handle Zn Options
        zn_options_set = set()
        for value in self.option_tracker.zn_options:
            zn_options_set.add(
                (f"--{value.dvc_parameter}", self.zn_outs_path / f"{value.option}.json")
            )
        for pair in zn_options_set:
            script += pair

        # Add command to run the script
        script.append(
            f"""{self.python_interpreter} -c "from {self.module} import {self.name}; """
            f"""{self.name}.load(name='{self.stage_name}').run_and_save()" """
        )
        log.debug(f"running script: {' '.join([str(x) for x in script])}")

        log.debug(
            "If you are using a jupyter notebook, you may not be able to see the "
            "output in real time!"
        )

        subprocess.check_call(script)

        # process = subprocess.run(script, capture_output=True, check=True)
        # if not silent:
        #     if len(process.stdout) > 0:
        #         log.info(process.stdout.decode())
        #     if len(process.stderr) > 0:
        #         log.warning(process.stderr.decode())


@dataclasses.dataclass
class ZnTrackOptionTracker:
    params: list[ZnTrackOption] = dataclasses.field(default_factory=list)
    dvc_options: list[ZnTrackOption] = dataclasses.field(default_factory=list)
    zn_options: list[ZnTrackOption] = dataclasses.field(default_factory=list)


class Node(abc.ABC):
    nb_name: str = None
    no_exec: bool = True
    silent: bool = False
    external: bool = False
    no_commit: bool = False

    has_metadata = False

    def __init__(
        self,
        name=None,
        no_exec: bool = True,
        external: bool = False,
        no_commit: bool = False,
        force: bool = True,
        always_changed: bool = False,
        no_run_cache: bool = False,
    ):
        dvc_options = DVCOptions(
            no_commit=no_commit,
            external=external,
            always_changed=always_changed,
            no_exec=no_exec,
            force=force,
            no_run_cache=no_run_cache,
        )
        self._zntrack = ZnTrack(self, name=name, dvc_options=dvc_options)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("Please see <migration tutorial>")

    @property
    def zntrack(self) -> ZnTrack:
        return self._zntrack

    def save(self):
        self.zntrack.save()

    def write_dvc(self):
        self.save()
        self.zntrack.write_dvc()

    @classmethod
    def load(cls, name=None) -> Node:
        # Load without using the init?
        # pass zntrack.NoneType to every args/kwargs - that will then be
        # ignored by dvc/zn.<option>. Also check if
        # NoneType in vars(MyNode(NoneType, NoneType, ...)).values()
        # and raise an error when trying to pass something that is not a parameter
        if name is None or name == cls.__name__:
            # If the  name was not changed by the user, they might not want to
            # use it, so instead of mandating 'super().__init__(name)' we ignore it,
            # if the name is equal to the cls name
            instance = cls()
        else:
            try:
                instance = cls(name=name)
            except TypeError:
                raise TypeError(
                    "Please check if name is passed to the super call. Otherwise add"
                    " '__init__(self, name=None)' and 'super().__init__(name=name)'."
                )

        instance.zntrack.load()
        return instance

    def run_and_save(self):
        self.run()
        self.save()

    # @abc.abstractmethod
    def run(self):
        raise NotImplementedError  #
