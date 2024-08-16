import typing as t
from ..config import ENV_FILE_PATH
import os
import yaml


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
