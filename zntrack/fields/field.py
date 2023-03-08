"""The base class for all fields."""
import abc
import json
import typing

import zninit

if typing.TYPE_CHECKING:
    from zntrack.core.node import Node


class Field(zninit.Descriptor, abc.ABC):
    """Base class for fields.

    Handles all the file I/O for the given field.

    Attributes
    ----------
    dvc_option : str
        The dvc command option for this field.
    """

    dvc_option: str = None

    @abc.abstractmethod
    def save(self, instance: "Node"):
        """Save the field to disk.

        Parameters
        ----------
        instance : Node
            The Node instance to save the field for.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def load(self, instance: "Node", lazy: bool = None):
        """Load the field from disk.

        Parameters
        ----------
        instance : Node
            The Node instance to load the field for.
        lazy : bool, optional
            Whether to load the field lazily, by default 'zntrack.config.lazy'.
        """
        raise NotImplementedError

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

    def _get_value_from_config(self, instance: "Node", decoder=None) -> any:
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
            instance.state.get_file_system().read_text("zntrack.json"),
        )
        return json.loads(json.dumps(zntrack_dict[instance.name][self.name]), cls=decoder)

    def _write_value_to_config(self, instance: "Node", encoder=None):
        """Write the value of this field to the zntrack config file.

        Parameters
        ----------
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
        zntrack_dict[instance.name][self.name] = instance.__dict__[self.name]
        # use the __dict__ to avoid the nwd replacement
        with open("zntrack.json", "w") as f:
            json.dump(zntrack_dict, f, indent=4, cls=encoder)
