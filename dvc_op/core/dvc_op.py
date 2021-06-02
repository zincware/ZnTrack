from __future__ import annotations
from typing import Union

import logging
import json
import subprocess
import yaml
from pathlib import Path

from typing import List

from .dataclasses import DVCParams, SlurmConfig, Files

log = logging.getLogger(__file__)


class DVCOp:
    def __init__(self, id_: Union[int, str] = None, filter_: dict = None):
        self._parameters: dict = {}
        self._id: int = 0
        self._running = False  # is set to true, when run_dvc
        self.dvc: DVCParams = DVCParams()
        self.slurm_config: SlurmConfig = SlurmConfig()

        self.json_file: bool = True

        self.config()

        if self.json_file:
            self._json_file = f"{self.name}.json"
        else:
            self._json_file = None

        try:
            if id_ is not None:
                self._update(self, str(id_))
            elif filter_ is not None:
                log.debug("Assuming that the filter only finds a single DVCOp!")
                for id_ in self.all_parameters:
                    stage_id = self._filter_parameters(filter_, id_)
                    if stage_id != -1:
                        self._update(self, stage_id)
                        break

        except KeyError:
            raise KeyError(f'Could not find a stage with id {id_}!')

    def config(self):
        """Set all arguments like DVCParams or SlurmConfig in here!"""
        pass
        # raise NotImplementedError("Implemented in child class")

    def __repr__(self):
        return self.dvc.__repr__()

    def run_dvc(self, id_=0):
        # TODO run_dvc should not take the id_ anymore, but the init should
        raise NotImplementedError('Implemented in child class')

    def post_call(self, force=False, exec_=False, always_changed=False, slurm=False):
        self.dvc.make_paths()
        self._write_parameters()
        self._write_dvc(force, exec_, always_changed, slurm)

    def pre_run(self, id_):
        # Note I am not using super run_dvc because run_dvc ALWAYS has to implemented in the child class!
        self._running = True
        self.id = id_
        self._update(self, id_)

    def _write_parameters(self):
        """Update parameters file

        Notes
        -----
        We use this method, because all_parameters is getting updated, so no information is lost.
        We can not write the parameters without caching the old / other parameters first
        """
        self.all_parameters = self.parameters

    @property
    def id(self) -> str:
        """Get multi_use id"""
        if self._running:
            return str(self._id)

        if self.dvc.multi_use:
            if len(self.all_parameters) == 0:  # no stage with this classes name found.
                log.debug(f"No Parameters for {self.name} found -> id=0")
                self._id = 0
            else:
                id_ = len(self.all_parameters)  # assume that the configuration is new and create a new id_
                for stage_id in self.all_parameters:
                    if self.all_parameters[stage_id] == self.parameters:
                        log.debug(f"Found stage with the given parameters for id = {stage_id}!")
                        id_ = stage_id  # entry already exists, load existing id_
                self._id = id_
        else:
            self._id = 0

        return str(self._id)

    @id.setter
    def id(self, value):
        if not self._running:
            raise ValueError('Can only set the value of id during dvc_run!')
        self._id = value

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def module(self) -> str:
        """Module from which to import <name>

        Used for from <module> import <name>
        """
        return self.__class__.__module__

    @property
    def stage_name(self) -> str:
        return f"{self.name}_{self.id}"

    @property
    def parameters(self) -> dict:
        if len(self._parameters) > 0:
            # Assume that the value is set, e.g. during the call method
            return self._parameters
        else:
            raise ValueError(
                'Something went wrong! Maybe you tried to change the parameters before creating them!'
                ' Always start with "self.parameters = [...]"')
            # # Try to read the value from a file, it it hasn't been set
            # try:
            #     return self.all_parameters[self.id]
            # except KeyError:
            #     return self._parameters  # == return {}

    @parameters.setter
    def parameters(self, value):
        self._parameters = value

    @property
    def all_parameters(self) -> dict:
        """Load ALL parameters from params_file"""
        try:
            with open(self.dvc.params_file_path / self.dvc.params_file) as json_file:
                return json.load(json_file)[self.name]
        except FileNotFoundError:
            log.debug(f"Could not load params from {self.dvc.params_file_path / self.dvc.params_file}!")
        except KeyError:
            log.debug(f"Stage with name {self.name} does not exist")
        return {}

    @all_parameters.setter
    def all_parameters(self, value):
        """Update parameters in params_file"""
        if isinstance(value, dict):
            try:
                with open(self.dvc.params_file_path / self.dvc.params_file) as json_file:
                    parameters = json.load(json_file)
            except FileNotFoundError:
                log.debug(f"Could not load params from {self.dvc.params_file_path / self.dvc.params_file}!")
                parameters = {}

            try:
                parameters[self.name].update({self.id: value})
                log.debug("Updating existing stage")
            except KeyError:
                log.debug(f"Creating a new stage for {self.name}")
                parameters.update({self.name: {self.id: value}})
            with open(self.dvc.params_file_path / self.dvc.params_file, "w") as json_file:
                json.dump(parameters, json_file)
        else:
            raise ValueError(f"Value has to be a dictionary but found {type(value)} instead!")

    @property
    def _dvc_file(self) -> dict:
        """Load ALL parameters from dvc.dvc_file"""
        try:
            with open(self.dvc.dvc_file) as json_file:
                return yaml.safe_load(json_file)
        except FileNotFoundError:
            log.debug(f"Could not load dvc config from {self.dvc.dvc_file}!")
        return {}

    @property
    def _dvc_stages(self) -> dict:
        """Load all stages from dvc.dvc_file"""
        return self._dvc_file['stages']

    @property
    def _dvc_stage(self) -> dict:
        """Load the current stage from dvc.dvc_file"""
        try:
            return self._dvc_stages[f"{self.name}_{self.id}"]
        except KeyError:
            return {}

    def _update(self, cls: DVCOp, id_: Union[int, str]):
        """Update all parameters of cls connected to the given id"""
        cls.parameters = self.all_parameters[str(id_)]
        log.debug("Updating Parameters!")
        try:
            cls.dvc.deps = [Path(x) for x in cls._dvc_stage['deps']]
            log.debug("Updating dependencies!")
        except KeyError:
            # No dependencies available
            pass

    def _get_obj_by_id(self, id_: int):
        """

        Parameters
        ----------
        id_: int
            Primary key

        Returns
        -------

        DVCOp:
            Returns a new instance of a DVCOp with the correct id

        """
        obj = self.__class__()

        self._update(obj, id_)

        # obj.parameters = self.all_parameters[self.name][str(id_)]  # need to convert int to str

        return obj

    def query_obj(self, filter_: Union[int, dict]) -> Union[DVCOp, List[DVCOp]]:
        """Get a class instance with all the available information attached

        Returns
        --------
        List[DVC_Op] : The instantiated class having self.parameters, self.id_ and potentially all post run parameters
                    set, so that it can be used

        Notes
        -----
        Most of the information will be in
            - self.parameters
            - self.results
        """

        if isinstance(filter_, int):
            return self._get_obj_by_id(filter_)
        else:
            objs = []

            ids = []
            for id_ in self.all_parameters:
                ids.append(self._filter_parameters(filter_, id_))

            for id_ in ids:
                if id_ == -1:
                    continue
                objs.append(self._get_obj_by_id(id_))

            return objs

    def _write_dvc(self, force=False, exec_: bool = False, always_changed: bool = False, slurm: bool = False):
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

        script = ['dvc', 'run', '-n', self.stage_name]

        script += self.files.get_dvc_arguments()

        script += ["--params", f"{self.dvc.params_file_path / self.dvc.params_file}:{self.name}.{self.id}"]

        if force:
            script.append("--force")
            log.warning("Overwriting existing configuration!")
            # TODO check these logs!
        #
        if not exec_:
            script.append("--no-exec")
        else:
            log.warning("You will not be able to see the stdout/stderr of the process in real time!")
        #
        if always_changed:
            script.append("--always-changed")
        #
        if slurm:
            log.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            log.warning("Make sure, that every stage uses SLURM! If a stage does not have SLURM enabled, the command "
                        "will be run on the HEAD NODE! Check the dvc.yaml file before running! There are no checks"
                        "implemented to test, that only SRUN is in use!")
            log.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            script.append('srun')
            script.append('-n')
            script.append(f"{self.slurm_config.n}")
        #
        script.append(f'python -c "from {self.module} import {self.name}; '
                      f'{self.name}().run_dvc(id_={self.id})"')
        log.debug(f"running script: {' '.join([str(x) for x in script])}")

        process = subprocess.run(script, shell=True, capture_output=True)
        if len(process.stdout) > 0:
            log.info(process.stdout.decode())
        if len(process.stderr) > 0:
            log.warning(process.stderr.decode())

    @property
    def files(self):
        """Return the files where to find.

        This is based on self.dvc and the self.id. This is only a property and can not be changed directly.
        Change the values in self.dvc for that! We use this function, because it combines the path, id and filenames
        from self.dvc

        Notes
        -----
        The user never has to handle the internal naming with the id attached. Ideally only the file names and not the
        paths are changed, that is why we provide self.dvc for configuration.
        """
        return Files(id_=self.id, dvc_params=self.dvc, json_file=self._json_file)

    @property
    def results(self) -> dict:
        try:
            with open(self.files.json_file) as f:
                file = json.load(f)
            return file
        except FileNotFoundError:
            log.warning("No results found!")
            return {}

    @results.setter
    def results(self, value):
        # TODO maybe make if self.files.json_file?!
        with open(self.files.json_file, "w") as f:
            json.dump(value, f)

    def _filter_parameters(self, filter_, id_) -> int:
        obj_id = -1
        for key, value in filter_.items():
            try:
                if self.all_parameters[id_][key] == value:
                    obj_id = id_
                else:
                    return -1
            except KeyError:
                log.debug(f"Can not find key '{key}' in 'all_parameters' - skipping!")
        return obj_id
