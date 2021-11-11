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

    # DVC Parameter
    deps: List[Path] = field(default_factory=list)
    # Has no path, because it always comes as a path object already

    outs: Union[List[Path], List[str]] = field(default_factory=list)

    outs_no_cache: Union[List[Path], List[str]] = field(default_factory=list)

    outs_persistent: Union[List[Path], List[str]] = field(default_factory=list)

    metrics: Union[List[Path], List[str]] = field(default_factory=list)

    metrics_no_cache: Union[List[Path], List[str]] = field(default_factory=list)

    plots: Union[List[Path], List[str]] = field(default_factory=list)

    plots_no_cache: Union[List[Path], List[str]] = field(default_factory=list)

    def get_dvc_arguments(self) -> list:
        """Combine the attributes with the corresponding DVC option

        Returns
        -------
        str: E.g. for outs it will return a list of
            ["--outs", "outs[0]", ...]

        """
        out = []

        for dvc_param in self.__dataclass_fields__:
            if dvc_param == "internals_file":
                continue
            processed_params = []
            for param_val in getattr(self, dvc_param):
                if param_val in processed_params:
                    log.debug(f"Parameter {dvc_param}:{param_val} found more than once")
                    continue
                if param_val is None:
                    # DVC can not process None, so we skip here but log it
                    log.warning(
                        f"Found {dvc_param} with value {param_val} that can"
                        f"not be processed - skipping it."
                    )
                    continue
                out += [f"--{dvc_param.replace('_', '-')}", param_val]

                processed_params.append(param_val)

        return out

    def get_affected_files(self) -> list:
        """Collects all files that this Node writes to

        Returns
        -------
        affected_files: list
            list of str/Path that this Node writes to
        """
        # Ignore dependencies, they will not be changed by this Node

        output_types = [
            x for x in self.__dataclass_fields__ if x not in ["deps", "internals_file"]
        ]
        affected_files = []
        for output_type in output_types:
            if getattr(self, output_type) is not None:
                file_list = getattr(self, output_type)
                # remove metadata from the affect files, because
                #  they should never be a dependency
                file_list = [x for x in file_list if x.name != "metadata.json"]
                affected_files += file_list
        return affected_files


@dataclass(frozen=False, order=True, init=True)
class ZnFiles:
    """Collection of ZnFiles

    Files that support load=true.
    These files will be stored in nodes/<node_name>/file


    Attributes
    ----------
    node_name: str
        Name of the node to create the directory
    directory: Path
        default directory for node outputs
    """

    node_name: str
    directory: Path = Path("nodes")

    outs: Path = Path("outs.json")
    outs_no_cache: Path = Path("outs_no_cache.json")
    outs_persistent: Path = Path("outs_persistent.json")
    metrics: Path = Path("metrics.json")
    metadata: Path = Path("metadata.json")
    metrics_no_cache: Path = Path("metrics_no_cache.json")
    plots: Path = Path("plots.json")
    plots_no_cache: Path = Path("plots_no_cache.json")

    def make_path(self):
        self.node_path.mkdir(parents=True, exist_ok=True)

    @property
    def node_path(self) -> Path:
        """Path to the directory where all files are stored"""
        return self.directory / self.node_name


@dataclass(frozen=True, order=True)
class SlurmConfig:
    """Available SLURM Parameters for SRUN"""

    n: int = 1
