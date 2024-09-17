import os
import pathlib
import typing as t

import yaml
import znflow.utils

from zntrack.utils.import_handler import import_handler

from ..config import ENV_FILE_PATH


def get_plugins_from_env(self):
    plugins_paths = os.environ.get(
        "ZNTRACK_PLUGINS", "zntrack.plugins.dvc_plugin.DVCPlugin"
    )
    plugins = [import_handler(p) for p in plugins_paths.split(",")]
    return {plugin.__name__: plugin(self) for plugin in plugins}


def get_attr_always_list(obj: t.Any, attr: str) -> list:
    value = getattr(obj, attr)
    if isinstance(value, dict):
        return list(value.values())
    if not isinstance(value, list):
        value = [value]
    return value


def load_env_vars(name: str | None = None) -> None:
    # TODO: this should also use DVCFileSystem!
    if ENV_FILE_PATH.exists():
        env = yaml.safe_load(ENV_FILE_PATH.read_text())
        global_config = env.get("global", {})
        for key, val in global_config.items():
            if isinstance(val, list):
                global_config[key] = ",".join(val)
            elif isinstance(val, str):
                pass
            elif val is None:
                pass
            else:
                raise ValueError(
                    f"variable '{key}' has an invalid value '{val}' ({type(val)})"
                )
        os.environ.update(global_config)

        for key, value in env.get("stages", {}).get(name, {}).items():
            if isinstance(value, str):
                os.environ[key] = value
            elif isinstance(value, dict):
                os.environ.update(value)
            elif value is None:
                pass
            else:
                raise ValueError(
                    f"variable '{key}' has an invalid value '{val}' ({type(val)})"
                )


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


def sort_key(item):
    """Custom sorting key function to handle both string and dictionary types."""
    if isinstance(item, str):
        return item
    elif isinstance(item, dict):
        # For dictionaries, sort by their first (and only) key's string representation
        return list(item.keys())[0]


def sort_and_deduplicate(data: list[str | dict[str, dict]]):
    """Sort and deduplicate a list of strings and dictionaries."""
    data = sorted(data, key=sort_key)

    new_data = []
    for key in data:
        if key not in new_data:
            if isinstance(key, dict):
                if next(iter(key.keys())) in new_data:
                    raise ValueError(
                        f"Duplicate key with different parameters found: {key}"
                    )
                for other_key in new_data:
                    if isinstance(other_key, dict):
                        if next(iter(other_key.keys())) == next(iter(key.keys())):
                            if other_key != key:
                                raise ValueError(
                                    f"Duplicate key with different parameters found: {key}"
                                )
            if isinstance(key, str):
                for other_key in new_data:
                    if isinstance(other_key, dict) and key in other_key.keys():
                        raise ValueError(
                            f"Duplicate key with different parameters found: {key}"
                        )
            new_data.append(key)

    return new_data
