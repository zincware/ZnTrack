"""DVC fields without serialization of data / for file paths."""
import pathlib
import typing

import znjson

from zntrack import Node
from zntrack.fields.field import Field
from zntrack.utils import nwd


class DVCOption(Field):
    """A field that is used as a dvc option.

    The DVCOption field is designed for paths only.
    """

    def __init__(self, *args, **kwargs):
        """Create a DVCOption field."""
        self.dvc_option = kwargs.pop("dvc_option")
        super().__init__(*args, **kwargs)

    def get_affected_files(self, instance: Node) -> list:
        """Get the files affected by this field."""
        value = getattr(instance, self.name)
        if not isinstance(value, list):
            value = [value]
        return [pathlib.Path(file).as_posix() for file in value]

    def get_stage_add_argument(self, instance: Node) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        return [
            (f"--{self.dvc_option}", file) for file in self.get_affected_files(instance)
        ]

    def load(self, instance: Node):
        """Load the field from config file."""
        return self._get_value_from_config(instance, decoder=znjson.ZnDecoder)

    def save(self, instance: Node):
        """Save the field to config file."""
        if instance.state.loaded:
            return  # Don't save if the node is loaded from disk
        self._write_value_to_config(instance, encoder=znjson.ZnEncoder)

    def __get__(self, instance: Node, owner=None):
        """Add replacemt of the nwd to the get method."""
        if instance is None:
            return self
        value = super().__get__(instance, owner)
        return nwd.ReplaceNWD()(value, nwd=instance.nwd)


def outs(*args, **kwargs) -> DVCOption:
    """Create a outs field."""
    return DVCOption(*args, dvc_option="outs", **kwargs)


def params(*args, **kwargs) -> DVCOption:
    """Create a params field."""
    return DVCOption(*args, dvc_option="params", **kwargs)


def deps(*args, **kwargs) -> DVCOption:
    """Create a deps field."""
    return DVCOption(*args, dvc_option="deps", **kwargs)


def outs_no_cache(*args, **kwargs) -> DVCOption:
    """Create a outs_no_cache field."""
    return DVCOption(*args, dvc_option="outs-no-cache", **kwargs)


def outs_persistent(*args, **kwargs) -> DVCOption:
    """Create a outs_persistent field."""
    return DVCOption(*args, dvc_option="outs-persistent", **kwargs)


def metrics(*args, **kwargs) -> DVCOption:
    """Create a metrics field."""
    return DVCOption(*args, dvc_option="metrics", **kwargs)


def metrics_no_cache(*args, **kwargs) -> DVCOption:
    """Create a metrics_no_cache field."""
    return DVCOption(*args, dvc_option="metrics-no-cache", **kwargs)


def plots(*args, **kwargs) -> DVCOption:
    """Create a plots field."""
    return DVCOption(*args, dvc_option="plots", **kwargs)


def plots_no_cache(*args, **kwargs) -> DVCOption:
    """Create a plots_no_cache field."""
    return DVCOption(*args, dvc_option="plots-no-cache", **kwargs)
