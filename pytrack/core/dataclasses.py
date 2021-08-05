"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack dataclasses
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Union, List

log = logging.getLogger(__file__)


@dataclass(frozen=False, order=True, init=True)
class DVCParams:
    # pytrack Parameter
    multi_use: bool = False
    params_file: str = "params.json"
    params_file_path: Path = Path("config")

    json_file: Union[Path, str, None] = None

    # DVC Parameter
    deps: List[Path] = field(default_factory=list)
    # Has no path, because it always comes as a path object already

    outs: Union[List[Path], List[str]] = field(default_factory=list)
    outs_path: Path = Path("outs")

    outs_no_cache: Union[List[Path], List[str]] = field(default_factory=list)
    outs_no_cache_path: Path = Path("outs")

    outs_persistent: Union[List[Path], List[str]] = field(default_factory=list)
    outs_persistent_path: Path = Path("outs")

    metrics: Union[List[Path], List[str]] = field(default_factory=list)
    metrics_path: Path = Path("metrics")

    metrics_no_cache: Union[List[Path], List[str]] = field(default_factory=list)
    metrics_no_cache_path: Path = Path("metrics")

    plots: Union[List[Path], List[str]] = field(default_factory=list)
    plots_path: Path = Path("plots")

    plots_no_cache: Union[List[Path], List[str]] = field(default_factory=list)
    plots_no_cache_path: Path = Path("plots")

    _dvc_params: List[str] = field(
        default_factory=lambda: [
            'deps', 'outs', 'outs_no_cache', 'outs_persistent', 'metrics', 'metrics_no_cache', 'plots',
            'plots_no_cache'
        ],
        init=False,
        repr=False)

    def __post_init__(self):
        self.outs = [self.outs_path / out for out in self.outs]
        if self.json_file is not None:
            self.json_file = self.outs_path / self.json_file

    def get_dvc_arguments(self) -> list:
        """Combine the attributes with the corresponding DVC option

        Returns
        -------
        str: E.g. for outs it will return a list of ["--outs", "outs_path/{id}_outs[0]", ...]

        """

        def flatten(x):
            """
            Convert [[str, Path], [str, Path]] to [str, Path, str, Path]
            """
            return sum(x, [])

        out = []

        for dvc_param in self._dvc_params:
            out.append(flatten([[f"--{dvc_param.replace('_', '-')}", x] for x in self.__dict__[dvc_param]]))

        if self.json_file is not None:
            out += [["--outs", self.json_file]]

        return flatten(out)

    def make_paths(self):
        """Create all paths that can possibly be used"""
        for key in self.__dict__:
            if key.endswith("path"):
                # self.__dict__[key]: Path
                if len(self.__dict__[key[:-5]]) > 0:
                    # Check if the corresponding list has an entry - if not, you don't need to create the folder
                    self.__dict__[key].mkdir(exist_ok=True, parents=True)

        if self.json_file is not None:
            self.outs_path.mkdir(exist_ok=True, parents=True)

    def load_from_file(self, json_file, dvc_stage: dict):
        for dvc_param in self._dvc_params:
            try:
                if json_file is not None and dvc_param == "outs":
                    outs = []
                    for stage_param in dvc_stage[dvc_param]:
                        if stage_param.endswith(json_file):
                            self.json_file = Path(stage_param)
                        else:
                            outs.append(Path(stage_param))
                    self.outs = outs
                else:
                    self.__dict__[dvc_param] = [Path(x) for x in dvc_stage[dvc_param]]
            except KeyError:
                pass


@dataclass(frozen=True, order=True)
class SlurmConfig:
    """Available SLURM Parameters for SRUN"""

    n: int = 1
