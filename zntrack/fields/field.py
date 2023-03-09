"""The base class for all fields."""
import abc
import enum
import json
import logging
import typing

import zninit

from zntrack.utils import LazyOption, config

if typing.TYPE_CHECKING:
    from zntrack.core.node import Node

log = logging.getLogger(__name__)


class FieldGroup(enum.Enum):
    """Characterizes the group of a field."""

    PARAMETER = enum.auto()
    RESULT = enum.auto()


class Field(zninit.Descriptor, abc.ABC):
    """Base class for fields.

    Handles all the file I/O for the given field.

    Attributes
    ----------
    dvc_option : str
        The dvc command option for this field.
    """

    dvc_option: str = None
    group: FieldGroup = None

    @abc.abstractmethod
    def save(self, instance: "Node"):
        """Save the field to disk.

        Parameters
        ----------
        instance : Node
            The Node instance to save the field for.
        """
        raise NotImplementedError

    def load(self, instance: "Node", lazy: bool = None):
        """Load the field from disk.

        Parameters
        ----------
        instance : Node
            The Node instance to load the field for.
        lazy : bool, optional
            Whether to load the field lazily.
            This only applies to 'LazyField' classes.
        """
        try:
            instance.__dict__[self.name] = self._get_value_from_file(instance)
        except FileNotFoundError:
            # if something was not loaded, we set the loaded state to False
            log.warning(f"Could not load field {self.name} for node {instance.name}.")
            instance.state.loaded = False

    @abc.abstractmethod
    def get_stage_add_argument(self, instance: "Node") -> typing.List[tuple]:
        """Get the dvc stage add argument for this field.

        Parameters
        ----------
        instance : Node
            The Node instance to get the stage add argument for.

        Returns
        -------
        typing.List[tuple]
            The stage add argument for this field.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_affected_files(self, instance: "Node") -> list:
        """Get the files affected by this field.

        Parameters
        ----------
        instance : Node
            The Node instance to get the affected files for.

        Returns
        -------
        list
            The affected files.
        """
        raise NotImplementedError

    def get_optional_dvc_cmd(self, instance: "Node") -> typing.List[str]:
        """Get optional dvc commands that will be executed beside the main dvc command.

        This could be 'plots modify ...' or 'stage add --name node_helper'

        Parameters
        ----------
        instance : Node
            The Node instance to get the optional dvc commands for.

        Returns
        -------
        typing.List[str]
            The optional dvc commands.
        """
        return []

    @abc.abstractmethod
    def _get_value_from_file(self, instance: "Node") -> any:
        """Get the value of the field from the file."""
        raise NotImplementedError

    def _write_value_to_config(self, value, instance: "Node", encoder=None):
        """Write the value of this field to the zntrack config file.

        Parameters
        ----------
        value: any
            The value to write to the config file.
        instance : Node
            The node instance to which this field belongs.
        encoder : json.JSONEncoder, optional
            The JSON encoder to use, by default None.

        """
        try:
            with open("zntrack.json", "r") as f:
                zntrack_dict = json.load(f)
        except FileNotFoundError:
            zntrack_dict = {}

        if instance.name not in zntrack_dict:
            zntrack_dict[instance.name] = {}
        zntrack_dict[instance.name][self.name] = value
        # use the __dict__ to avoid the nwd replacement
        with open("zntrack.json", "w") as f:
            json.dump(zntrack_dict, f, indent=4, cls=encoder)


class LazyField(Field):
    """Base class for fields that are loaded lazily."""

    def __get__(self, instance, owner=None):
        """Load the field from disk if it is not already loaded."""
        if instance is None:
            return self
        if instance.__dict__.get(self.name) is LazyOption:
            self.load(instance, lazy=False)

        return super().__get__(instance, owner)

    def load(self, instance: "Node", lazy: bool = None):
        """Load the field from disk.

        Parameters
        ----------
        instance : Node
            The Node instance to load the field for.
        lazy : bool, optional
            Whether to load the field lazily, by default 'zntrack.config.lazy'.
        """
        if lazy in [None, True] and config.lazy:
            instance.__dict__[self.name] = LazyOption
        else:
            super().load(instance)
