from dataclasses import dataclass, field
from pathlib import Path
from typing import Union


@dataclass(frozen=True, order=True)
class Files:
    deps: list[Path]
    outs: list[Path]
    outs_no_cache: list[Path]
    outs_persistent: list[Path]
    params: list[Path]
    metrics: list[Path]
    metrics_no_cache: list[Path]
    plots: list[Path]
    plots_no_cache: list[Path]

    json_file: Union[Path, None] = None

    def get_dvc_arguments(self) -> list:
        def flatten(x):
            """
            Convert [[str, Path], [str, Path]] to [str, Path, str, Path]
            """
            return sum(x, [])

        out = []

        for option in self.__dict__:
            try:
                out.append(
                    flatten([[f"--{option.replace('_', '-')}", x] for x in self.__dict__[option]])
                )
            except TypeError:
                # reached json_file which is not iterable!
                pass
        if self.json_file is not None:
            out += [['--outs', self.json_file]]

        return flatten(out)


@dataclass(frozen=True, order=True)
class DVCParams:
    # DVCOp Parameter
    multi_use: bool = False
    params_file: str = 'params.json'
    params_file_path: Path = Path("config")

    dvc_file: str = "dvc.yaml"

    # DVC Parameter
    deps: list[str] = field(default_factory=list)
    deps_path: Path = Path("deps")

    outs: list[str] = field(default_factory=list)
    outs_path: Path = Path("outs")

    outs_no_cache: list[str] = field(default_factory=list)
    outs_no_cache_path: Path = Path("outs")

    outs_persistent: list[str] = field(default_factory=list)
    outs_persistent_path: Path = Path("outs")

    params: list[str] = field(default_factory=list)
    params_path: Path = Path("params")

    metrics: list[str] = field(default_factory=list)
    metrics_path: Path = Path("metrics")

    metrics_no_cache: list[str] = field(default_factory=list)
    metrics_no_cache_path: Path = Path("metrics")

    plots: list[str] = field(default_factory=list)
    plots_path: Path = Path("plots")

    plots_no_cache: list[str] = field(default_factory=list)
    plots_no_cache_path: Path = Path("plots")

    def make_paths(self):
        """Create all paths that can possibly be used"""
        for key in self.__dict__:
            if key.endswith('path'):
                # self.__dict__[key]: Path
                if len(self.__dict__[key[:-5]]) > 0:
                    # Check if the corresponding list has an entry - if not, you don't need to create the folder
                    self.__dict__[key].mkdir(exist_ok=True, parents=True)


@dataclass(frozen=True, order=True)
class SlurmConfig:
    n: int = 1
