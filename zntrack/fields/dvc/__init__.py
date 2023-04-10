"""DVC fields without serialization of data / for file paths."""
import json
import pathlib
import typing

import znjson

from zntrack.fields.field import Field, FieldGroup, PlotsMixin
from zntrack.utils import node_wd

if typing.TYPE_CHECKING:
    from zntrack import Node


class DVCOption(Field):
    """A field that is used as a dvc option.

    The DVCOption field is designed for paths only.
    """

    group = FieldGroup.PARAMETER

    def __init__(self, *args, **kwargs):
        """Create a DVCOption field."""
        self.dvc_option = kwargs.pop("dvc_option")
        super().__init__(*args, **kwargs)

    def get_files(self, instance: "Node") -> list:
        """Get the files affected by this field.

        Parameters
        ----------
        instance : Node
            The node instance to get the files for.

        Returns
        -------
        list of str
            A list of file paths affected by this field.

        """
        value = getattr(instance, self.name)
        if not isinstance(value, list):
            value = [value]
        return [pathlib.Path(file).as_posix() for file in value if file is not None]

    def get_stage_add_argument(self, instance: "Node") -> typing.List[tuple]:
        """Get the dvc command for this field.

        Parameters
        ----------
        instance : Node
            The node instance to get the command for.

        Returns
        -------
        list of tuple of str
            A list of command-line arguments to use when adding
            this field to the DVC stage.

        """
        if self.dvc_option == "params":
            return [
                (f"--{self.dvc_option}", f"{file}:") for file in self.get_files(instance)
            ]
        else:
            return [(f"--{self.dvc_option}", file) for file in self.get_files(instance)]

    def get_data(self, instance: "Node") -> any:
        """Get the value of the field from the configuration file.

        Parameters
        ----------
        instance : Node
            The Node instance to get the field value for.
        decoder : Any, optional
            The decoder to use when parsing the configuration file, by default None.

        Returns
        -------
        any
            The value of the field from the configuration file.
        """
        zntrack_dict = json.loads(
            instance.state.fs.read_text("zntrack.json"),
        )
        return json.loads(
            json.dumps(zntrack_dict[instance.name][self.name]), cls=znjson.ZnDecoder
        )

    def save(self, instance: "Node"):
        """Save the field to config file.

        Parameters
        ----------
        instance : Node
            The node instance to save the field for.

        """
        try:
            value = instance.__dict__[self.name]
        except KeyError:
            try:
                # default value is not stored in __dict__
                # TODO: not sure if I like this
                value = getattr(instance, self.name)
            except AttributeError:
                return
        self._write_value_to_config(value, instance, encoder=znjson.ZnEncoder)

    def __get__(self, instance: "Node", owner=None):
        """Add replacement of the nwd to the get method.

        Parameters
        ----------
        instance : Node
            The node instance to get the value for.
        owner : type, optional
            The owner class of the descriptor, by default None

        Returns
        -------
        Any
            The value of the attribute.

        """
        if instance is None:
            return self
        value = super().__get__(instance, owner)
        return node_wd.ReplaceNWD()(value, nwd=instance.nwd)


class PlotsOption(PlotsMixin, DVCOption):
    """Field with DVC plots kwargs."""


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
    return PlotsOption(*args, dvc_option="plots", **kwargs)


def plots_no_cache(*args, **kwargs) -> DVCOption:
    """Create a plots_no_cache field."""
    return PlotsOption(*args, dvc_option="plots-no-cache", **kwargs)
