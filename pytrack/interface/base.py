"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
import logging
import subprocess
import json
from typing import List
from pathlib import Path

log = logging.getLogger(__name__)


class DVCInterface:
    """A Python Interface for DVC"""

    def __init__(self, dvc_path: str = "."):
        """DVCInterface for getting experiments and loading data from multiple experiments

        Parameters
        ----------
        dvc_path: str
                Path to the DVC repository to use
        """
        self.dvc_path = dvc_path
        self._experiments = None
        self._exp_dict = None

    @property
    def experiments(self) -> dict:
        """Get all experiments in json format"""
        if self._experiments is None:
            # Only load it once! This speeds things up. If experiments change during the lifetime
            # of this instance they won't be registered except _reset is called!
            cmd = ["dvc", "exp", "show", "--show-json", "-A"]
            log.debug(f"DVC command: {cmd}")
            out = subprocess.run(cmd, capture_output=True, cwd=self.dvc_path)
            self._experiments = json.loads(out.stdout)
        return self._experiments

    @property
    def exp_dict(self) -> dict:
        """Get all experiment names and hash values

        Returns
        -------
        dict: A dictionary containing {name: hash}
        """
        if self._exp_dict is None:
            exp_dict = {}
            for key, workspace in self.experiments.items():
                if key == "workspace":
                    continue
                for exp in workspace:
                    if exp == "baseline":
                        try:
                            exp_dict[workspace[exp]["name"]] = key
                        except KeyError:
                            exp_dict[key] = key
                    else:
                        try:
                            exp_dict[workspace[exp]["name"]] = exp
                        except KeyError:
                            exp_dict[key] = exp
            self._exp_dict = exp_dict
        return self._exp_dict

    def _reset(self):
        """Reset properties to be loaded again"""
        self._experiments = None
        self._exp_dict = None

    def load_files_into_directory(
        self, files: List[str], path: str = "experiments", experiments: List[str] = None
    ):
        """Save files from multiple experiments in a single directory

        Create a parent directory "path" that contains subdirectories for each experiment where the requested
        files are saved.

        Parameters
        ----------
        files: list
            A list of files or directories to load into path
        path: str
            The  path where the files should be saved at. If the path is not absolute it is always relative
            to the dvc_path!
        experiments: list, default=None
            A list of experiment names to query. If None all experiments will be loaded.

        """
        path = Path(path)
        path.mkdir(exist_ok=True, parents=True)
        if experiments is None:
            exp_dict = self.exp_dict
        else:
            exp_dict = {}
            for key in experiments:
                try:
                    exp_dict[key] = self.exp_dict[key]
                except KeyError:
                    raise KeyError(
                        f" '{key}' could not be found in the list of experiments"
                    )

        for experiment in exp_dict:
            for file in files:
                out_path = path / experiment
                out_path.mkdir(parents=True, exist_ok=True)
                cmd = [
                    "dvc",
                    "get",
                    ".",
                    file,
                    "--rev",
                    exp_dict[experiment],
                    "--out",
                    out_path,
                ]
                log.debug(f"DVC command: {cmd}")
                subprocess.run(cmd, cwd=self.dvc_path)
