"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
import copy
import dataclasses
import json
import logging
import subprocess
from pathlib import Path
from typing import List

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Experiment:
    """Collection of the output of dvc exp show --show-json"""

    name: str
    hash: str
    timestamp: str
    queued: bool
    running: bool
    executor: str
    params: dict
    metrics: dict


class DVCInterface:
    """A Python Interface for DVC"""

    def __init__(self):
        """DVCInterface for getting experiments and loading data from
        multiple experiments
        """
        self._experiments = None
        self._exp_list = None

    @property
    def experiments(self) -> dict:
        """Get all experiments in json format"""
        if self._experiments is None:
            # Only load it once! This speeds things up. If experiments change
            # during the lifetime of this instance they won't be
            # registered except _reset is called!
            cmd = ["dvc", "exp", "show", "--show-json", "-A"]
            log.debug(f"DVC command: {cmd}")
            out = subprocess.run(cmd, capture_output=True)
            self._experiments = json.loads(out.stdout.decode("utf-8").split("\r\n")[0])
        return self._experiments

    @property
    def exp_list(self) -> List[Experiment]:
        """Get all experiment names and hash values for the current commit

        Returns
        -------
        list[Experiment]: A list containing experiment dataclasses
        """

        if self._exp_list is None:
            experiments = copy.deepcopy(self.experiments)
            experiments.pop("workspace")
            experiment_dict = next(iter(experiments.values()))

            exp_list = []
            for key, vals in experiment_dict.items():
                if key == "baseline":
                    key = next(iter(experiments))
                exp_list.append(Experiment(hash=key, **vals["data"]))

            self._exp_list = exp_list
        return self._exp_list

    def _reset(self):
        """Reset properties to be loaded again"""
        self._experiments = None
        self._exp_list = None

    def load_files_into_directory(
        self, files: List[str], path: str = "experiments", experiments: List[str] = None
    ):
        """Save files from multiple experiments in a single directory

        Create a parent directory "path" that contains subdirectories for each
        experiment where the requested files are saved.

        Parameters
        ----------
        files: list
            A list of files or directories to load into path.
        path: str
            The  path where the files should be saved at. If the path is not absolute
            it is always relative to the dvc_path!
        experiments: list, default=None
            A list of experiment names to query. If None all experiments will be loaded.

        """
        path = Path(path)
        path.mkdir(exist_ok=True, parents=True)
        if experiments is None:
            exp_list = self.exp_list
        else:
            exp_list = [x for x in self.exp_list if x.name in experiments]

        for experiment in exp_list:
            for file in files:
                out_path = path / experiment.name
                out_path.mkdir(parents=True, exist_ok=True)
                cmd = [
                    "dvc",
                    "get",
                    ".",
                    file,
                    "--rev",
                    experiment.hash,
                    "--out",
                    out_path,
                ]
                log.debug(f"DVC command: {cmd}")
                subprocess.run(cmd)
