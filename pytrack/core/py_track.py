"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack core
"""

from __future__ import annotations

import logging
import subprocess
import yaml

from .data_classes import SlurmConfig
from .parameter import PyTrackOption
from pytrack.core.data_classes import DVCParams
from pathlib import Path

log = logging.getLogger(__name__)


class PyTrackParent:
    """Parent class to be applied within the decorator"""

    def __init__(self, child):
        """Constructor for the DVCOp parent class"""
        log.debug(f"New instance of {self} with {child}")
        self.child = child

        # Parameters that will be overwritten by "child" classes
        self.slurm_config: SlurmConfig = SlurmConfig()

        # Properties
        self._id: int = 0
        self._running = False  # is set to true, when run_dvc
        self._module = None
        self._stage_name = None

        self.dvc_file = "dvc.yaml"
        self.was_called = False
        self.allow_param_change = False
        self.allow_result_change = False
        self.is_init = False
        # This is True while inside the init to avoid ValueErrors

        self.dvc = DVCParams()
        self.nb_mode = False  # notebook mode

    def pre_init(self, load: bool = False):
        """Function to be called prior to the init

        Parameters
        ----------
        load: bool
            Load the stage and prohibit parameter changes
        """
        if not load:
            self.allow_param_change = True
        self.is_init = True

        log.debug(f"Setting param change to {self.allow_param_change} on {self}")

    def post_init(self):
        """Post init command

        This command is executed after the init of the "child" class.
        It handles:
        - updating which attributes are parameters and results

        """
        # Updating internals and checking for parameters and results
        self.update_dvc_options()
        if self.has_results():
            self.dvc.set_json_file(f"{self.id}_{self.name}.json")

        self.is_init = False

    def pre_call(self):
        """Method to be run before the call"""
        if self.was_called:
            raise AttributeError(
                "This method was already called. Please create a new instance!"
            )

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

        self.dvc.make_paths()

        self._write_dvc(force, exec_, always_changed, slurm)

        self.was_called = True
        self.allow_param_change = False

    def pre_run(self):
        """Command to be run before run

        Updates internals.

        Notes
        -----
         Not using super run_ because run ALWAYS has to implemented in the child class
         and should otherwise raise and error!

        """
        self.update_dvc()
        self.dvc.make_paths()
        # required if your are inside a temporary directory
        self.allow_result_change = True
        self._running = True

    def post_run(self):
        """Method to be executed after run

        This method saves the results
        """
        self.allow_result_change = False

    def update_dvc_options(self):
        """Update the dvc_options with None values

        This is run after the __init__ to save all DVCParams and they can later be
        overwritten
        """
        for attr, value in vars(self.child).items():
            try:
                option = value.pytrack_dvc_option
                # this is not hard coded, because when overwriting
                # PyTrackOption those custom descriptors also need to be applied!

                value: PyTrackOption  # or child instances
                py_track_option = value.__class__
                try:
                    log.debug(
                        f"Updating {attr} with PyTrackOption and value {value.value}!"
                    )
                    setattr(
                        type(self.child),
                        attr,
                        py_track_option(
                            option=option, value=value.value, attr=attr, cls=self.child
                        ),
                    )
                except AttributeError:
                    raise AttributeError("setattr went wrong!")
            except AttributeError:
                pass

    @property
    def id(self) -> str:
        """Get multi_use id"""
        if self._running:
            return str(self._id)

        self._id = 0

        return str(self._id)

    def update_dvc(self):
        """Update the DVCParams with the options from self.dvc

        This method searches for all PyTrackOptions that are defined within the __init__
        """
        for attr, val in vars(type(self.child)).items():
            if isinstance(val, PyTrackOption):
                option = val.pytrack_dvc_option
                new_vals = getattr(self.child, attr)
                try:
                    if isinstance(new_vals, list):
                        [getattr(self.dvc, option).append(x) for x in new_vals]
                    else:
                        getattr(self.dvc, option).append(new_vals)
                except AttributeError:
                    log.debug(f"'DVCParams' object has no attribute '{option}'")

    def has_results(self) -> bool:
        """Check if a json file is generated by looking for defined results"""
        for attr, val in vars(type(self.child)).items():
            if isinstance(val, PyTrackOption):
                if val.pytrack_dvc_option == "result":
                    return True
        return False

    def has_params(self) -> bool:
        """Check if any params are required by going through the defined params"""
        for attr, val in vars(type(self.child)).items():
            if isinstance(val, PyTrackOption):
                if val.pytrack_dvc_option == "params":
                    return True
        return False

    def _write_dvc(
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
                f"{self.dvc.internals_file}:{self.name}.{self.id}.params",
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

    @id.setter
    def id(self, value):
        """Change id if self._running

        Parameters
        ----------
        value: int
            New id

        """
        if not self._running:
            raise ValueError("Can only set the value of id during dvc_run!")
        self._id = value

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
        """
        if self._module is None:
            self._module = self.child.__class__.__module__
        return self._module

    @property
    def stage_name(self) -> str:
        """Get the stage name"""
        if self._stage_name is None:
            self._stage_name = f"{self.name}_{self.id}"

        return self._stage_name

    @stage_name.setter
    def stage_name(self, value):
        """Set the stage name"""
        self._stage_name = value

    @property
    def dvc_stages(self) -> dict:
        """Load all stages from dvc.dvc_file"""
        with open(self.dvc_file, "r") as f:
            dvc_file = yaml.safe_load(f)

        return dvc_file["stages"]

    @property
    def dvc_stage(self) -> dict:
        """Load the current stage from dvc.dvc_file"""
        try:
            return self.dvc_stages[f"{self.name}_{self.id}"]
        except KeyError:
            return {}
