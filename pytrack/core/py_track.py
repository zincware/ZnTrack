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

log = logging.getLogger(__file__)


class PyTrackParent:
    def __init__(self):
        """Constructor for the DVCOp parent class
        """

        # Parameters that will be overwritten by "child" classes
        self.slurm_config: SlurmConfig = SlurmConfig()

        # Conventions
        # self._pytrack_<placeholder> is considered a normal attribute
        # self._pytrack__<placeholder> is considered a hidden attribute

        # Properties
        self._pytrack__id: int = 0
        self._pytrack__running = False  # is set to true, when run_dvc
        self._pytrack__module = None

        self._pytrack_dvc_file = 'dvc.yaml'
        self._pytrack_was_called = False
        self._pytrack_allow_param_change = False
        self._pytrack_allow_result_change = False

        self._pytrack_dvc = DVCParams()
        self._pytrack_nb_mode = False

    def _pytrack_pre_init(self, id_):
        self._pytrack_allow_param_change = id_ is None

    def _pytrack_post_init(self):
        """Post init command

        This command is executed after the init of the "child" class.
        It handles:
        - updating which attributes are parameters and results
        - loads values if id_!=None

        Parameters
        ----------
        id_:int
            Either None if new stage or usually 0 if a stage should be loaded

        Returns
        -------

        """
        # Updating internals and checking for parameters and results
        self._pytrack_update_dvc_options()
        self._pytrack_dvc.set_json_file(f"{self._pytrack_id}_{self._pytrack_name}.json")

    def _pytrack_pre_call(self):
        """Method to be run before the call"""
        # TODO only allow setting DVC.<placeholder> in the call method, excpet for results which are only allowed in run
        if self._pytrack_was_called:
            raise AttributeError('This method was already called. Please create a new instance!')

    def _pytrack_post_call(self, force=False, exec_=False, always_changed=False, slurm=False):
        """Method after call

        This function should always be the last one in the __call__ method, it handles file IO and DVC execution

        Parameters
        ----------
        force: bool, default=False
            Use dvc run with `--force` to overwrite previous stages!
        exec_: bool, default=False
            Run the stage directly and don't use dvc with '--no-exec'.
            This will not output stdout/stderr in real time and should only be used for fast functions!
        always_changed: bool, default=False
            Set the always changed dvc argument. See the official DVC docs. Can be useful for debugging / development.
        slurm: bool, default=False
            Use `SRUN` with self.slurm_config for this stage - WARNING this doesn't mean that every stage uses slurm
            and you may accidentally run stages on your HEAD Node. You can check the commands in dvc.yaml!

        """
        self._pytrack_dvc.make_paths()

        self._write_dvc(force, exec_, always_changed, slurm)

        self._pytrack_was_called = True

    def _pytrack_pre_run(self):
        """Command to be run before run

        Updates internals.

        Notes
        -----
         Not using super run_ because run ALWAYS has to implemented in the child class and should otherwise
         raise and error!

        """
        self._pytrack_allow_result_change = True
        self._pytrack__running = True

    def _pytrack_post_run(self):
        """Method to be executed after run

        This method saves the results
        """
        self._pytrack_allow_result_change = False

    def _pytrack_update_dvc_options(self):
        """Update the dvc_options with None values

        This is run after the __init__ to save all DVCParams and they can later be overwritten
        """
        for attr, value in vars(self).items():
            try:
                option = value.pytrack_dvc_option
                try:
                    log.warning(f"Updating {attr} with PyTrackOption and value {value.value}!")
                    setattr(type(self), attr, PyTrackOption(option=option, value=value.value, attr=attr, cls=self))
                except AttributeError:
                    raise AttributeError('setattr went wrong!')
            except AttributeError:
                pass

    @property
    def _pytrack_id(self) -> str:
        """Get multi_use id"""
        if self._pytrack__running:
            return str(self._pytrack__id)

        self._pytrack__id = 0

        return str(self._pytrack__id)

    def _pytrack_update_dvc(self):
        for attr, val in vars(type(self)).items():
            if isinstance(val, PyTrackOption):
                if val.pytrack_dvc_option == "outs":
                    # TODO check that this works with lists!
                    self._pytrack_dvc.outs.append(getattr(self, attr))
                if val.pytrack_dvc_option == "deps":
                    # TODO check that this works with lists!
                    self._pytrack_dvc.deps.append(getattr(self, attr))

    def _write_dvc(
            self,
            force=True,
            exec_: bool = False,
            always_changed: bool = False,
            slurm: bool = False,
    ):
        """Write the DVC file using run.

        If it already exists it'll tell you that the stage is already persistent and has been run before.
        Otherwise it'll run the stage for you.

        Parameters
        ----------
        force: bool, default = False
            Force DVC to rerun this stage, even if the parameters haven't changed!
        exec_: bool, default = False
            if False, only write the stage to the dvc.yaml and run later. Otherwise the stage and ALL dependencies
            will be executed!
        always_changed: bool, default = False
            Tell DVC to always rerun this stage, e.g. for non-deterministic stages or for testing
        slurm: bool, default = False
            Use SLURM to run DVC stages on a Cluster.

        Notes
        -----
        If the dependencies for a stage change this function won't necessarily tell you.
        Use 'dvc status' to check, if the stage needs to be rerun.

        """

        self._pytrack_update_dvc()

        script = ["dvc", "run", "-n", self._pytrack_stage_name]

        script += self._pytrack_dvc.get_dvc_arguments()
        # TODO if no DVC.result are assigned, no json file will be written!

        script += [
            "--params",
            f"{self._pytrack_dvc.internals_file}:{self._pytrack_name}.{self._pytrack_id}.params",
        ]

        if self._pytrack_nb_mode:
            script += ["--deps", Path(*self._pytrack_module.split(".")).with_suffix(".py")]

        if force:
            script.append("--force")
            log.warning("Overwriting existing configuration!")
        #
        if not exec_:
            script.append("--no-exec")
        else:
            log.warning(
                "You will not be able to see the stdout/stderr of the process in real time!"
            )
        #
        if always_changed:
            script.append("--always-changed")
        #
        if slurm:
            log.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            log.warning(
                "Make sure, that every stage uses SLURM! If a stage does not have SLURM enabled, the command "
                "will be run on the HEAD NODE! Check the dvc.yaml file before running! There are no checks"
                "implemented to test, that only SRUN is in use!"
            )
            log.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            script.append("srun")
            script.append("-n")
            script.append(f"{self.slurm_config.n}")
        #
        script.append(
            f'{self._pytrack_python_interpreter} -c "from {self._pytrack_module} import {self._pytrack_name}; '
            f'{self._pytrack_name}(id_={self._pytrack_id}).run()"'
        )
        log.debug(f"running script: {' '.join([str(x) for x in script])}")

        log.debug(
            "If you are using a jupyter notebook, you may not be able to see the output in real time!"
        )
        process = subprocess.run(script, capture_output=True)
        if len(process.stdout) > 0:
            log.info(process.stdout.decode())
        if len(process.stderr) > 0:
            log.warning(process.stderr.decode())

    @property
    def _pytrack_python_interpreter(self):
        """Find the most suitable python interpreter

        Try to run subprocess check calls to see, which python interpreter should be selected

        Returns
        -------
        interpreter: str
            Name of the python interpreter that works with subprocess calls

        """

        for interpreter in ["python3", "python"]:
            try:
                subprocess.check_call([interpreter, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log.debug(f"Using command {interpreter} for dvc!")
                return interpreter

            except subprocess.CalledProcessError:
                log.debug(f"{interpreter} is not working!")
        raise ValueError(
            "Could not find a working python interpreter to work with subprocesses!"
        )

    @_pytrack_id.setter
    def _pytrack_id(self, value):
        """Change id if self._running

        Parameters
        ----------
        value: int
            New id

        """
        if not self._pytrack__running:
            raise ValueError("Can only set the value of id during dvc_run!")
        self._pytrack__id = value

    @property
    def _pytrack_name(self) -> str:
        """Used for naming the stage and dvc run

        Returns
        -------
        str: Name of this class

        """
        return self.__class__.__name__

    @property
    def _pytrack_module(self) -> str:
        """Module from which to import <name>

        Used for from <module> import <name>
        """
        if self._pytrack__module is None:
            self._pytrack__module = self.__class__.__module__
        return self._pytrack__module

    @property
    def _pytrack_stage_name(self) -> str:
        """Get the stage name"""
        return f"{self._pytrack_name}_{self._pytrack_id}"

    @property
    def _pytrack_dvc_stages(self) -> dict:
        """Load all stages from dvc.dvc_file"""
        with open(self._pytrack_dvc_file, "r") as f:
            dvc_file = yaml.safe_load(f)

        return dvc_file["stages"]

    @property
    def _pytrack_dvc_stage(self) -> dict:
        """Load the current stage from dvc.dvc_file"""
        try:
            return self._pytrack_dvc_stages[f"{self._pytrack_name}_{self._pytrack_id}"]
        except KeyError:
            return {}
