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
        return self._get_value_from_config(instance, decoder=znjson.ZnDecoder)

    def save(self, instance: Node):
        if instance.state.loaded:
            return  # Don't save if the node is loaded from disk
        self._write_value_to_config(instance, encoder=znjson.ZnEncoder)


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
