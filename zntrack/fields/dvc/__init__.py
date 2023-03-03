import functools
import json
import pathlib
import typing

import znjson

from zntrack import Node
from zntrack.fields.field import Field

# from znflow import get_attribute as getattr



class DVCOption(Field):
    def __init__(self, *args, **kwargs):
        self.dvc_option = kwargs.pop("dvc_option")
        super().__init__(*args, **kwargs)

    def get_affected_files(self, instance: Node) -> list:
        value = getattr(instance, self.name)
        if not isinstance(value, list):
            value = [value]
        return [pathlib.Path(file).as_posix() for file in value]

    def get_stage_add_argument(self, instance: Node) -> typing.List[tuple]:
        return [
            (f"--{self.dvc_option}", file) for file in self.get_affected_files(instance)
        ]

    def load(self, instance: Node):
        zntrack_dict = json.loads(
            instance.state.get_file_system().read_text("zntrack.json"),
        )
        instance.__dict__[self.name] = json.loads(
            json.dumps(zntrack_dict[instance.name][self.name]),
            cls=znjson.ZnDecoder,
        )

    def save(self, instance: Node):
        if instance.state.loaded:
            return  # Don't save if the node is loaded from disk
        try:
            zntrack_dict = json.loads(pathlib.Path("zntrack.json").read_text())
        except FileNotFoundError:
            zntrack_dict = {}

        if instance.name not in zntrack_dict:
            zntrack_dict[instance.name] = {}
        zntrack_dict[instance.name][self.name] = getattr(instance, self.name)
        pathlib.Path("zntrack.json").write_text(
            json.dumps(zntrack_dict, indent=4, cls=znjson.ZnEncoder)
        )


def outs(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="outs", **kwargs)


def params(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="params", **kwargs)


def deps(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="deps", **kwargs)


def outs_no_cache(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="outs-no-cache", **kwargs)


def outs_persistent(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="outs-persistent", **kwargs)


def metrics(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="metrics", **kwargs)


def metrics_no_cache(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="metrics-no-cache", **kwargs)


def plots(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="plots", **kwargs)


def plots_no_cache(*args, **kwargs) -> DVCOption:
    return DVCOption(*args, dvc_option="plots-no-cache", **kwargs)
