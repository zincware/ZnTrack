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
import json

from zntrack.utils import is_jsonable, deserializer, serializer

log = logging.getLogger(__name__)


@dataclass(frozen=False, order=True, init=True)
class DVCOptions:
    """Extension to the DVCParams

    DVCParams handles e.g. I/O whilst DVCOptions handles all other parameters,
    such as the name, exec, force, commit, external, ...

    See Also
    --------
    https://dvc.org/doc/command-reference/run
    """

    no_commit: bool = False
    external: bool = False
    always_changed: bool = False
    no_exec: bool = False
    force: bool = False
    no_run_cache: bool = False

    @property
    def dvc_arguments(self) -> list:
        """Get the activated options

        Returns
        -------
        list: A list of strings for the subprocess call
            ["--no-commit", "--external"]

        """
        out = []

        for dvc_option in self.__dataclass_fields__:
            value = getattr(self, dvc_option)
            if isinstance(value, bool):
                if value:
                    out.append(f"--{dvc_option.replace('_', '-')}")
                else:
                    if dvc_option == "no_exec":
                        log.warning(
                            "You will not be able to see the stdout/stderr "
                            "of the process in real time!"
                        )
            else:
                raise NotImplementedError("Currently only boolean values are supported")

        return out


@dataclass(frozen=False, order=True, init=True)
class DVCParams:
    """PyTracks DVCParams"""

    # Node Parameter
    node_name: str
    internals_path: Path = Path("config")

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

    @property
    def internals_file(self) -> Path:
        """Path to the parameter file"""
        return self.internals_path / f"{self.node_name}.json"

    def update(self, value, option):
        """Update internals

        Update the selected internal (by option) with the given value.
        In the case of a ZnTrackOption it will update via the affected files.

        Parameters
        ----------
        value:
            Either a str/path to a file or a ZnTrackType class
            where all ZnTrackType.affected_files will be added to the dependencies
        option: str
            A DVC option e.g. outs, or metric_no_cache, ...

        """
        try:
            value.zntrack.dvc: DVCParams
            # Check if the passed value is a Node. If yes
            #  add all affected files as dependencies
            value.zntrack.update_dvc()
            log.debug(f"Found Node dependency. Calling update_dvc on {value}")
            dvc_option_list = getattr(self, option)
            dvc_option_list += value.zntrack.dvc.affected_files
            setattr(self, option, dvc_option_list)
        except AttributeError:
            try:
                getattr(self, option).append(value)
            except AttributeError:
                # descriptors_from_file / params will be skipped
                #  they are not part of the dataclass.
                log.debug(f"'DVCParams' object has no attribute '{option}'")

    @property
    def dvc_arguments(self) -> list:
        """Combine the attributes with the corresponding DVC option

        Returns
        -------
        str: E.g. for outs it will return a list of
            ["--outs", "outs[0]", ...]

        """
        out = []

        for dvc_param in self.__dataclass_fields__:
            if dvc_param in ["internals_path", "node_name"]:
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
                # Always convert to posix path
                out += [f"--{dvc_param.replace('_', '-')}", Path(param_val).as_posix()]

                processed_params.append(param_val)

        return out

    @property
    def affected_files(self) -> list:
        """Collects all files that this Node writes to

        This will contain the stage.json for descriptors_from_file, but also
        all outs, plot, metrics, ... and also all files changed by
        zn.<option>

        Returns
        -------
        affected_files: list
            list of str/Path that this Node writes to
        """
        # Ignore dependencies, they will not be changed by this Node

        output_types = [
            x for x in self.__dataclass_fields__ if x not in ["deps", "internals_path", "node_name"]
        ]
        affected_files = []
        for output_type in output_types:
            if getattr(self, output_type) is not None:
                file_list = getattr(self, output_type)
                # remove metadata from the affect files, because
                #  they should never be a dependency
                file_list = [x for x in file_list if Path(x).name != "metadata.json"]
                affected_files += file_list
        return affected_files

    @property
    def internals(self) -> dict:
        """Load the content of the internals_file as dict

        Returns
        -------
        dict:
            JSON content of internals file converted to a dict.
            When the file is not available it will return an empty dict
        """
        try:
            return json.loads(self.internals_file.read_text())
        except FileNotFoundError:
            log.debug(f"Could not load params from {self.internals_file}!")
            return {}

    @internals.setter
    def internals(self, value: dict):
        """Update the internals_file

        Save the content of value to the internals file.
        This will overwrite the file entirely and therefore it must be updated /
        read in before writing to it.
        """
        log.debug(f"Saving dvc.internals {value}")

        if not is_jsonable(value):
            raise ValueError(f"{value} is not JSON serializable")

        self.internals_file.parent.mkdir(exist_ok=True, parents=True)
        self.internals_file.write_text(json.dumps(value, indent=4))


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

    @property
    def node_path(self) -> Path:
        """Path to the directory where all files are stored"""
        return self.directory / self.node_name

    def make_path(self):
        """Create the directory for the nodes outputs"""
        self.node_path.mkdir(parents=True, exist_ok=True)

    @property
    def internals(self) -> dict:
        """Load all zn.<options> from files and deserialize them

        Returns
        -------
        dict:
            A dictionary of the de-serialized zn.<options> in form of a dictionary
            {option_name: value}

        """
        data = {}
        for option in self.__dataclass_fields__:
            file = self.node_path / getattr(self, option)
            try:
                data.update(deserializer(json.loads(file.read_text())))
            except FileNotFoundError:
                log.debug(f"No descriptors_from_file found for {option}!")

        return data

    @internals.setter
    def internals(self, values: dict):
        """Save all zn.<options> into the respective files

        Parameters
        ----------
        values: dict
            A dictionary of {option_name, values} that will be serialized and saved
            into the corresponding json file
        """
        for option, values in values.items():
            # At least one file will be written -> create the directory
            self.make_path()
            file = self.node_path / getattr(self, option)

            data = serializer(values)
            if not is_jsonable(data):
                raise ValueError(f"{data} is not JSON serializable")
            log.debug(f"Writing {file} to {file}")

            file.write_text(json.dumps(data, indent=4))


@dataclass(frozen=True, order=True)
class SlurmConfig:
    """Available SLURM Parameters for SRUN"""

    n: int = 1
