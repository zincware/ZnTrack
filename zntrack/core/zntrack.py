"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Node core
"""

from __future__ import annotations

import logging
import subprocess
import json

from .data_classes import SlurmConfig
from .parameter import ZnTrackOption
from zntrack.core.data_classes import DVCParams
from pathlib import Path
from zntrack.utils import is_jsonable, serializer, deserializer
from zntrack.utils.types import ZnTrackType, ZnTrackStage

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zntrack.utils.type_hints import TypeHintParent

log = logging.getLogger(__name__)


class ZnTrackProperty:
    """Map the correct zntrack instance to the correct cls

    This is required, because we use setattr(TYPE(cls)) and not on the
    instance, so we need to distinguish between different instances,
    otherwise there is only a single cls.zntrack for all instances!

    We save the Node instance in self.__dict__ to avoid this.
    """

    def __get__(self, instance, owner):
        """

        Parameters
        ----------
        instance: TypeHintParent
            An instance of the decorated function
        owner

        Returns
        -------
        Node:
            the zntrack property to handle Node
        """
        try:
            return instance.__dict__["zntrack"]
        except KeyError:
            instance.__dict__["zntrack"] = ZnTrackParent(instance)
            return instance.__dict__["zntrack"]

    def __set__(self, instance, value):
        raise NotImplementedError("Can not change zntrack property!")


class ZnTrackParent(ZnTrackType):
    """Parent class to be applied within the decorator"""

    def __init__(self, child):
        """Constructor for the DVCOp parent class"""
        log.debug(f"New instance of {self} with {child}")
        self.child: TypeHintParent = child

        # Parameters that will be overwritten by "child" classes
        self.slurm_config: SlurmConfig = SlurmConfig()

        # Properties

        self._module = None
        self._stage_name = None

        self.running = False  # is set to true, when run_dvc
        self.load = False

        self.dvc_file = "dvc.yaml"
        # This is True while inside the init to avoid ValueErrors

        self.dvc = DVCParams()
        self.nb_mode = False  # notebook mode

    def pre_init(self):
        """Function to be called prior to the init"""
        self.dvc.set_json_file(self.name)

    def post_init(self):
        """Post init command

        This command is executed after the init of the "child" class.
        It handles:
        - updating which attributes are parameters and results

        """
        self.fix_zntrackoptions()
        if self.load:
            self.load_internals()
            self.load_results()

    def pre_call(self):
        """Method to be run before the call"""
        if self.load:
            raise ValueError("This stage is being loaded and can not be called.")

    def post_call(self, force=False, exec_=False, always_changed=False, slurm=False):
        """Method after call

        This function should always be the last one in the __call__ method,
        it handles file IO and DVC execution

        Parameters
        ----------
        force: bool, default=False
            Use dvc run with `--force` to overwrite previous stages!
        exec_: bool, default=False
            Run the stage directly and don't use dvc with '--no-exec'.
            This will not output stdout/stderr in real time and should only be used
            for fast functions!
        always_changed: bool, default=False
            Set the always changed dvc argument. See the official DVC docs.
            Can be useful for debugging / development.
        slurm: bool, default=False
            Use `SRUN` with self.slurm_config for this stage - WARNING this doesn't
            mean that every stage uses slurm and you may accidentally run stages on
            your HEAD Node. You can check the commands in dvc.yaml!

        """
        self.update_dvc()

        self.write_dvc(force, exec_, always_changed, slurm)

        self.save_internals()

    def pre_run(self):
        """Command to be run before run

        Updates internals.

        Notes
        -----
         Not using super run_ because run ALWAYS has to implemented in the child class
         and should otherwise raise and error!

        """
        self.dvc.make_paths()
        # required if your are inside a temporary directory
        self.running = True

    def post_run(self):
        """Method to be executed after run

        This method saves the results
        """
        self.save_results()
        self.save_results()

    def fix_zntrackoptions(self):
        """Fix ZnTrackOption as attribute of the parent class

        This is required, if the znTrackOption is defined inside the __init__
        because that means :code:`ZnTrackOption in vars(hello_world)` but we require
        :code:`ZnTrackOption in vars(hello_world.__class__)` so with this code we update
        the parent class

        Notes
        -----
        It should be preferred to set them not in the __init__ but under the class
        definition to make them parts of the parent class
            >>> class HelloWorld:
            >>>     option=ZnTrackOption()


        """

        remove_from__dict__ = []

        for attr, value in vars(self.child).items():
            if isinstance(value, ZnTrackOption):
                # this is not hard coded, because when overwriting
                # ZnTrackOption those custom descriptors also need to be applied!
                log.warning(
                    f"DeprecationWarning: please move the definition "
                    f"of {attr} from __init__ to class level!"
                )

                log.debug(
                    f"Updating {attr} with {value.option} / {attr} "
                    f"and default {value.default_value}"
                )

                value: ZnTrackOption  # or child instances
                ParsedZnTrackOption = value.__class__
                try:
                    log.debug(f"Updating {attr} with ZnTrackOption!")

                    py_track_option = ParsedZnTrackOption(
                        option=value.option,
                        default_value=value.default_value,
                        name=attr,
                    )

                    setattr(type(self.child), attr, py_track_option)
                    remove_from__dict__.append(attr)
                except ValueError:
                    log.warning(f"Skipping {attr} update - might already be fixed!")

        # Need to remove them from __dict__, because when setting them inside
        #  the __init__ the __dict__ is set and we don't want that!
        for attr in remove_from__dict__:
            log.debug(f"removing: {self.child.__dict__.pop(attr, None)} ")

    def update_dvc(self):
        """Update the DVCParams with the options from self.dvc

        This method searches for all ZnTrackOptions that are defined within the __init__
        """
        log.debug(f"checking for instance {self.child}")
        for attr, val in vars(type(self.child)).items():
            if isinstance(val, ZnTrackOption):
                option = val.option
                new_vals = getattr(self.child, attr)
                log.debug(f"processing {attr} - {new_vals}")
                # check if it is a stage, that has to be handled extra
                if hasattr(new_vals, "zntrack"):
                    if isinstance(new_vals.zntrack, ZnTrackParent):
                        getattr(self.dvc, option).append(new_vals.zntrack.dvc.json_file)
                else:
                    try:
                        if isinstance(new_vals, list):
                            [getattr(self.dvc, option).append(x) for x in new_vals]
                        else:
                            getattr(self.dvc, option).append(new_vals)
                    except AttributeError:
                        # results / params will be skipped
                        log.debug(f"'DVCParams' object has no attribute '{option}'")

    def has_params(self) -> bool:
        """Check if any params are required by going through the defined params"""
        for attr, val in vars(type(self.child)).items():
            if isinstance(val, ZnTrackOption):
                if val.option == "params":
                    return True
        return False

    def write_dvc(
        self,
        force=True,
        exec_: bool = False,
        always_changed: bool = False,
        slurm: bool = False,
    ):
        """Write the DVC file using run.

        If it already exists it'll tell you that the stage is already persistent and
        has been run before. Otherwise it'll run the stage for you.

        Parameters
        ----------
        force: bool, default = False
            Force DVC to rerun this stage, even if the parameters haven't changed!
        exec_: bool, default = False
            if False, only write the stage to the dvc.yaml and run later.
             Otherwise the stage and ALL dependencies will be executed!
        always_changed: bool, default = False
            Tell DVC to always rerun this stage, e.g. for non-deterministic stages
            or for testing
        slurm: bool, default = False
            Use SLURM to run DVC stages on a Cluster.

        Notes
        -----
        If the dependencies for a stage change this function won't necessarily tell you.
        Use 'dvc status' to check, if the stage needs to be rerun.

        """
        log.warning("--- Writing new DVC file! ---")

        script = ["dvc", "run", "-n", self.stage_name]

        script += self.dvc.get_dvc_arguments()
        # TODO if no DVC.result are assigned, no json file will be written!

        if self.has_params():
            script += [
                "--params",
                f"{self.dvc.internals_file}:{self.stage_name}.params",
            ]

        if self.nb_mode:
            script += ["--deps", Path(*self.module.split(".")).with_suffix(".py")]

        if force:
            script.append("--force")
            log.warning("Overwriting existing configuration!")
        #
        if not exec_:
            script.append("--no-exec")
        else:
            log.warning(
                "You will not be able to see the stdout/stderr "
                "of the process in real time!"
            )
        #
        if always_changed:
            script.append("--always-changed")
        #
        if slurm:
            log.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            log.warning(
                "Make sure, that every stage uses SLURM! If a stage does not have SLURM"
                " enabled, the command will be run on the HEAD NODE! Check the dvc.yaml"
                " file before running! There are no checks implemented to test, "
                "that only SRUN is in use!"
            )
            log.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            script.append("srun")
            script.append("-n")
            script.append(f"{self.slurm_config.n}")
        #
        script.append(
            f'{self.python_interpreter} -c "from {self.module} import {self.name}; '
            f'{self.name}(load=True).run()"'
        )
        log.debug(f"running script: {' '.join([str(x) for x in script])}")

        log.debug(
            "If you are using a jupyter notebook, you may not be able to see the "
            "output in real time!"
        )
        process = subprocess.run(script, capture_output=True)
        if len(process.stdout) > 0:
            log.info(process.stdout.decode())
        if len(process.stderr) > 0:
            log.warning(process.stderr.decode())

    @property
    def python_interpreter(self):
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
        """Used for naming the stage and dvc run

        Returns
        -------
        str: Name of this class

        """
        return self.child.__class__.__name__

    @property
    def module(self) -> str:
        """Module from which to import <name>

        Used for from <module> import <name>

        Notes
        -----
        this can be changed when using nb_mode
        """
        if self._module is None:
            self._module = self.child.__class__.__module__
        return self._module

    @property
    def stage_name(self) -> str:
        """Get the stage name"""
        if self._stage_name is None:
            return self.name
        return self._stage_name

    @stage_name.setter
    def stage_name(self, value):
        """Set the stage name"""
        self._stage_name = value

    def save_internals(self):
        """Write all changed internals to file

        Update e.g. the parameters, out paths, etc. in the zntrack.json file
        """
        full_internals = self.internals_from_file
        log.debug(f"Serializing {self.internals}")
        full_internals[self.stage_name] = serializer(self.internals)
        log.debug(f"Saving {full_internals[self.stage_name]}")
        self.internals_from_file = full_internals

    def save_results(self):
        """Save the results to the json file

        Notes
        -----
        Adding the executed=True to ensure that a json file is always being saved
        """
        results = serializer(self.results)

        if not is_jsonable(results):
            raise ValueError(f"{results} is not JSON serializable")
        log.debug(f"Writing {results} to {self.dvc.json_file}")

        results["executed"] = True

        self.dvc.json_file.write_text(json.dumps(results, indent=4))

    def load_internals(self):
        """Load the internals from the zntrack.json file"""
        try:
            log.debug(f"un-serialize {self.internals_from_file[self.stage_name]}")
            self.internals = deserializer(self.internals_from_file[self.stage_name])
        except KeyError:
            log.warning(f"No internals found for {self.stage_name}")

    def load_results(self):
        """Load the results from file"""
        try:
            self.results = deserializer(json.loads(self.dvc.json_file.read_text()))
        except FileNotFoundError:
            log.warning("No results found!")

    @property
    def results(self) -> dict:
        """Get all ZnTrackOption results and combine them in a single dict"""
        results = {}
        for attr, val in vars(type(self.child)).items():
            if isinstance(val, ZnTrackOption):
                if val.option == "result":
                    results[val.name] = getattr(self.child, attr)
        return results

    @results.setter
    def results(self, value: dict):
        """Set the values for the results in the __dict__ attribute of the child

        Parameters
        ----------
        value: dict
            {result1: val1, result2: val2, ...}
        """
        for key, val in value.items():
            self.child.__dict__[key] = val

    @property
    def internals(self):
        """Get all ZnTrackOptions (except results)"""
        internals = {}
        for attr, val in vars(type(self.child)).items():
            if isinstance(val, ZnTrackOption):
                if val.option == "result":
                    continue
                option_dict = internals.get(val.option, {})
                option_dict[val.name] = getattr(self.child, attr)

                internals[val.option] = option_dict

        return internals

    @internals.setter
    def internals(self, value: dict):
        """Save all ZnTrackOptions/Internals (except results)

        Stores all passed options in the child.__dict__

        Parameters
        ----------
        value: dict
            {param: {param1: val1, ...}, deps: {deps1: val1, ...}}
        """
        for option in value.values():
            for key, val in option.items():
                if isinstance(val, ZnTrackStage):
                    # Load the ZnTrackStage
                    self.child.__dict__[key] = val.get()
                else:
                    # Everything except the ZnTrackStage
                    self.child.__dict__[key] = val

    @property
    def internals_from_file(self) -> dict:
        """Load ALL internals from .zntrack.json"""
        try:
            with open(self.dvc.internals_file) as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            log.debug(f"Could not load params from {self.dvc.internals_file}!")
        return {}

    @internals_from_file.setter
    def internals_from_file(self, value: dict):
        """Update internals in .zntrack.json"""
        log.debug(f"Writing updates to .zntrack.json as {value}")
        value.update({"default": None})

        if not is_jsonable(value):
            raise ValueError(f"{value} is not JSON serializable")

        Path(self.dvc.internals_file).parent.mkdir(exist_ok=True, parents=True)

        self.dvc.internals_file.write_text(json.dumps(value, indent=4))
