"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack core
"""

from __future__ import annotations
from typing import Union, List

import logging
import json
import subprocess
import yaml
from pathlib import Path
import abc

from .data_classes import DVCParams, SlurmConfig
from .parameter import ParameterHandler
from pytrack.utils import is_jsonable

log = logging.getLogger(__file__)


class PyTrackParent:
    def __init__(self):
        """Constructor for the DVCOp parent class

        Parameters
        ----------
        id_: int, str, optional
            Optional primary key to query a previously created stage
        filter_: dict, optional
            Optional second method to query - only executed if id_ = None - using a dictionary with parameters key pairs
            This will always return the first instance. If multiple instances are possible use query_obj()!
        """

        # Parameters that will be overwritten by "child" classes
        self.slurm_config: SlurmConfig = SlurmConfig()

        # Conventions
        # self._pytrack_<placeholder> is considered a normal attribute
        # self._pytrack__<placeholder> is considered a hidden attribute

        # Properties
        self._pytrack__id: int = 0
        self._pytrack__running = False  # is set to true, when run_dvc
        self._pytrack__dvc = None
        self._pytrack__module = None

        self._pytrack__parameters = {}
        self._pytrack__results = {}

        self._pytrack_json_file = None
        self._pytrack_dvc_file = 'dvc.yaml'

        self._pytrack_ph = ParameterHandler()

    def _pytrack_post_init(self, id_=None):
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

        self._pytrack_ph.update_dvc_options(self)

        if len(self._pytrack_ph.dvc_options['result']) > 0:
            self._pytrack_ph.dvc.set_json_file(f"{self._pytrack_id}_{self._pytrack_name}.json")

        # We update the internal dvc to the one the user defined

        # self._pytrack_dvc = self.dvc

        # TODO dvc restructure
        try:
            if id_ is not None:
                self._pytrack__id = id_
                # TODO setting a hidden variable should be done via the property setter
                for name, value in self._pytrack_parameters.items():
                    log.debug(f"Updating {name} with {value}")
                    self.__dict__.update({name: value})

                for name, value in self._pytrack_results.items():
                    log.debug(f"Updating {name} with {value}")
                    self.__dict__.update({name: value})

                # If we load a stage we read the dependcies from a file, so we reset them first
                # TODO check this here too
                self._pytrack_load_dvc()

        except KeyError:
            raise KeyError(f"Could not find a stage with id {id_}!")

    def _pytrack_pre_call(self):
        """Method to be run before the call"""
        pass

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
        # In here you can just overwrite everything from the init in self._pytrack_ph.dvc
        # if nothing new is added, it should be alright
        # If the user made changes to the dvc it will be applied to the internal one, which should
        # always be up-to-date. Then we change it to be absolut paths again.
        # self._pytrack_dvc = self.dvc
        # TODO update e.g. dependencies that are added within the call!

        self._pytrack_ph.dvc.make_paths()

        # Parameters are only set in/after the call method!
        self._pytrack_ph.update_dvc(self)

        self._pytrack_parameters = self._pytrack_ph.dvc_values['parameter']

        self._write_dvc(force, exec_, always_changed, slurm)

    def _pytrack_pre_run(self):
        """Command to be run before run

        Updates internals.

        Notes
        -----
         Not using super run_ because run ALWAYS has to implemented in the child class and should otherwise
         raise and error!

        """

        self._pytrack__running = True

    def _pytrack_load_dvc(self):
        for out_name, out_value in zip(
                self._pytrack_ph.dvc_options.get('out', []),
                self._pytrack_dvc_stage['outs']
        ):
            self.__dict__[out_name] = Path(out_value)

    def _pytrack_post_run(self):
        """Method to be executed after run

        This method saves the results
        """
        if self._pytrack_ph.dvc.json_file is not None:
            results = {}
            for result in self._pytrack_ph.dvc_options['result']:
                if is_jsonable(vars(self)[result]):
                    results.update({result: vars(self)[result]})
                else:
                    raise ValueError(f'Result {result} is not json serializable!')

            self._pytrack_results = results

    @property
    def _pytrack_results(self):
        """Result property to load the results as a dictionary
        """
        if self._pytrack_ph.dvc.json_file is not None:
            try:
                with open(self._pytrack_ph.dvc.json_file) as f:
                    file = json.load(f)
                return file
            except FileNotFoundError:
                log.warning("No results found!")
                return {}
        else:
            return {}

    @_pytrack_results.setter
    def _pytrack_results(self, value):
        """Write the results to a file

        Parameters
        ----------
        value: json
            values to be written to the json file

        Returns
        -------

        """
        with open(self._pytrack_ph.dvc.json_file, "w") as f:
            json.dump(value, f, indent=4)

    @property
    def _pytrack_parameters(self):
        """Get the parameters for this instance (Stage & Id)"""
        return self._pytrack_all_parameters.get(self._pytrack_name, {}).get(self._pytrack_id, {})

    @_pytrack_parameters.setter
    def _pytrack_parameters(self, value: dict):
        """Set the parameters for this instance (Stage & Id)

        This writes them to self._pytrack_all_parameters, i.e., to the config file.
        """
        if isinstance(value, dict):
            try:
                with open(
                        self._pytrack_ph.dvc.params_file
                ) as json_file:
                    parameters = json.load(json_file)
            except FileNotFoundError:
                log.debug(
                    f"Could not load params from {self._pytrack_ph.dvc.params_file}!"
                )
                parameters = {}

            try:
                parameters[self._pytrack_name] = {self._pytrack_id: value}
                # parameters[self._pytrack_name].update({self._pytrack_id: value})
                # TODO should this be an update or not better full replacement
                log.debug("Updating existing stage")
            except KeyError:
                log.debug(f"Creating a new stage for {self._pytrack_name}")
                parameters.update({self._pytrack_name: {self._pytrack_id: value}})

            self._pytrack_all_parameters = parameters

        else:
            raise ValueError(
                f"Value has to be a dictionary but found {type(value)} instead!"
            )

    @property
    def _pytrack_all_parameters(self) -> dict:
        """Load ALL parameters from params_file"""
        try:
            with open(self._pytrack_ph.dvc.params_file) as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            log.debug(
                f"Could not load params from {self._pytrack_ph.dvc.params_file}!"
            )
        except KeyError:
            log.debug(f"Stage with name {self._pytrack_name} does not exist")
        return {}

    @_pytrack_all_parameters.setter
    def _pytrack_all_parameters(self, value):
        """Update parameters in params_file"""
        with open(
                self._pytrack_ph.dvc.params_file, "w"
        ) as json_file:
            json.dump(value, json_file, indent=4)

    @property
    def _pytrack_id(self) -> str:
        """Get multi_use id"""
        if self._pytrack__running:
            return str(self._pytrack__id)

        # if self._pytrack_dvc.multi_use:
        #     raise NotImplementedError('Multiuse is not implemented in this version!')
        # else:
        self._pytrack__id = 0

        return str(self._pytrack__id)

    @property
    def _pytrack_dvc(self):
        """Return the files where to find.

        This is based on self.dvc and the self.id. This is only a property and can not be changed directly.
        Change the values in self.dvc for that! We use this function, because it combines the path, id and filenames
        from self.dvc

        Notes
        -----
        The user never has to handle the internal naming with the id attached. Ideally only the file names and not the
        paths are changed, that is why we provide self.dvc for configuration.
        """
        # TODO
        if self._pytrack__dvc is None:
            if self._pytrack_json_file is not None:
                json_file = f"{self._pytrack_id}_{self._pytrack_json_file}"
            else:
                json_file = None

            dvc = DVCParams()
            dvc.load_from_file(json_file, self._pytrack_dvc_stage)
            self._pytrack__dvc = dvc
        return self._pytrack__dvc

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

        script = ["dvc", "run", "-n", self._pytrack_stage_name]

        script += self._pytrack_ph.dvc.get_dvc_arguments()

        script += [
            "--params",
            f"{self._pytrack_ph.dvc.params_file}:{self._pytrack_name}.{self._pytrack_id}",
        ]

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
        raise subprocess.CalledProcessError(
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
