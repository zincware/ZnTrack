"""DVC Interface through ZnTrack."""
import copy
import dataclasses
import json
import logging
import pathlib
import re
import subprocess
from pathlib import Path
from typing import List

import tqdm

from zntrack import utils

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Experiment:
    """Collection of the output of dvc exp show --show-json."""

    name: str
    hash: str
    timestamp: str
    queued: bool
    running: bool
    executor: str
    params: dict
    metrics: dict
    deps: str = ""
    outs: str = ""


class DVCInterface:
    """A Python Interface for DVC."""

    @utils.deprecated(
        reason=(
            "The 'DVCInterface' is currently unmaintained and might be removed "
            "in a future release. It might not be compatible with newer DVC versions"
        ),
        version="0.4.3",
    )
    def __init__(self):
        """DVCInterface for getting experiments and loading data."""
        self._experiments = None
        self._exp_list = None

    @property
    def experiments(self) -> dict:
        """Get all experiments in json format."""
        if self._experiments is None:
            # Only load it once! This speeds things up. If experiments change
            # during the lifetime of this instance they won't be
            # registered except _reset is called!
            cmd = ["dvc", "exp", "show", "--show-json", "-A"]
            log.debug(f"DVC command: {cmd}")
            out = subprocess.run(cmd, capture_output=True, check=True)
            decodec_out = out.stdout.decode("utf-8")
            # we match everything before the last }}}} closes the json string and is
            # followed by some unwanted characters
            json_string = re.findall(r".*\}\}\}\}", decodec_out)[0]

            self._experiments = json.loads(json_string)
        return self._experiments

    @property
    def exp_list(self) -> List[Experiment]:
        """Get all experiment names and hash values for the current commit.

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
        """Reset properties to be loaded again."""
        self._experiments = None
        self._exp_list = None

    def load_files_into_directory(
        self, files: List[str], path: str = "experiments", experiments: List[str] = None
    ):
        """Save files from multiple experiments in a single directory.

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
            exp_list = [x for x in self.exp_list if x.name not in ("master", "main")]
        else:
            exp_list = [x for x in self.exp_list if x.name in experiments]

        progress_bar = tqdm.tqdm(exp_list)

        for experiment in progress_bar:
            progress_bar.set_description(f"Processing {experiment.name}")
            for file in files:
                file = pathlib.Path(file)
                out_path = path / experiment.name
                out_path.mkdir(parents=True, exist_ok=True)
                cmd = [
                    "get",
                    ".",
                    file.as_posix(),
                    "--rev",
                    experiment.hash,
                    "--out",
                    out_path.as_posix(),
                ]
                log.debug(f"DVC command: {cmd}")
                utils.run_dvc_cmd(cmd)
