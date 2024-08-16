import os
import pathlib
import typing as t

import yaml
import znflow.utils

from ..config import ENV_FILE_PATH


def get_attr_always_list(obj: t.Any, attr: str) -> list:
    value = getattr(obj, attr)
    if not isinstance(value, list):
        value = [value]
    return value


def load_env_vars(name: str):
    if ENV_FILE_PATH.exists():
        env = yaml.safe_load(ENV_FILE_PATH.read_text())
        os.environ.update(env.get("global", {}))

        for key, value in env.get("stages", {}).get(name, {}).items():
            if isinstance(value, str):
                os.environ[key] = value
            elif isinstance(value, dict):
                os.environ.update(value)
            elif value is None:
                pass
            else:
                raise ValueError(f"Unknown value for env variable {key}: {value}")


class TempPathLoader(znflow.utils.IterableHandler):
    def default(self, value, **kwargs):
        instance = kwargs["instance"]
        path = value

        if instance.state.fs.isdir(pathlib.Path(path).as_posix()):
            instance.state.fs.get(
                pathlib.Path(path).as_posix(),
                instance.state.tmp_path.as_posix(),
                recursive=True,
            )
            _path = instance.state.tmp_path / pathlib.Path(path).name
        else:
            temp_file = instance.state.tmp_path / pathlib.Path(path).name
            instance.state.fs.get(pathlib.Path(path).as_posix(), temp_file.as_posix())
            _path = temp_file

        if isinstance(path, pathlib.PurePath):
            return _path
        else:
            return _path.as_posix()
