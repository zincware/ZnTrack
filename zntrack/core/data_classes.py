"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Node dataclasses
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, List

log = logging.getLogger(__name__)


@dataclass(frozen=False, order=True, init=True)
class DVCParams:
    """PyTracks DVCParams"""

    # Node Parameter
    internals_file: Path = Path("config", "zntrack.json")

    json_file: Union[Path, str, None] = None

    # DVC Parameter
    deps: List[Path] = field(default_factory=list)
    # Has no path, because it always comes as a path object already

    outs: Union[List[Path], List[str]] = field(default_factory=list)
    outs_path: Path = Path("outs")

    outs_no_cache: Union[List[Path], List[str]] = field(default_factory=list)

    outs_persistent: Union[List[Path], List[str]] = field(default_factory=list)

    metrics: Union[List[Path], List[str]] = field(default_factory=list)

    metrics_no_cache: Union[List[Path], List[str]] = field(default_factory=list)

    plots: Union[List[Path], List[str]] = field(default_factory=list)

    plots_no_cache: Union[List[Path], List[str]] = field(default_factory=list)

    # TODO maybe remove this:
    _dvc_params: List[str] = field(
        default_factory=lambda: [
            "deps",
            "outs",
            "outs_no_cache",
            "outs_persistent",
            "metrics",
            "metrics_no_cache",
            "plots",
            "plots_no_cache",
        ],
        init=False,
        repr=False,
    )

    def __post_init__(self):
        """Combine the DVC Parameter with their associated path."""
        if self.json_file is not None:
            self.json_file = self.outs_path / self.json_file

    def get_dvc_arguments(self) -> list:
        """Combine the attributes with the corresponding DVC option

        Returns
        -------
        str: E.g. for outs it will return a list of
            ["--outs", "outs[0]", ...]

        """
        out = []

        for dvc_param in self._dvc_params:
            for param_val in getattr(self, dvc_param):
                if param_val is None:
                    # DVC can not process None, so we skip here but log it
                    log.warning(
                        f"Found {dvc_param} with value {param_val} that can"
                        f"not be processed - skipping it."
                    )
                    continue
                out += [f"--{dvc_param.replace('_', '-')}", param_val]

        if self.json_file is not None:
            out += ["--outs", self.json_file]

        return out

    def make_paths(self):
        """Create all paths that can possibly be used"""
        if self.json_file is not None:
            self.outs_path.mkdir(exist_ok=True, parents=True)

    def set_json_file(self, name):
        """

        Parameters
        ----------
        name: str
            The name of the json file, e.g. 0_Stage.json

        Returns
        -------

        """
        self.json_file = self.outs_path / f"{name}.json"
        self.outs_path.mkdir(exist_ok=True, parents=True)


@dataclass(frozen=True, order=True)
class SlurmConfig:
    """Available SLURM Parameters for SRUN"""

    n: int = 1
