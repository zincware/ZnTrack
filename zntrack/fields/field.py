"""The base class for all fields."""
import abc
import json
import pathlib
import typing

import zninit

if typing.TYPE_CHECKING:
    from zntrack.core.node import Node


class Field(zninit.Descriptor, abc.ABC):
    """A field for a Node.

    This class handles all the file I/O for the given field.
    """

    dvc_option: str = None

    @abc.abstractmethod
    def save(self, instance: "Node"):
        """Save the field to disk."""
        raise NotImplementedError

    @abc.abstractmethod
    def load(self, instance: "Node"):
        """Load the field from disk."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_stage_add_argument(self, instance: "Node") -> typing.List[tuple]:
        """Get the dvc stage add argument for this field."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_affected_files(self, instance: "Node") -> list:
        """Get the files affected by this field."""
        raise NotImplementedError

    def _get_value_from_config(self, instance: "Node", decoder=None) -> any:
        zntrack_dict = json.loads(
            instance.state.get_file_system().read_text("zntrack.json"),
        )
        return json.loads(json.dumps(zntrack_dict[instance.name][self.name]), cls=decoder)

    def _write_value_to_config(self, instance: "Node", encoder=None):
        try:
            zntrack_dict = json.loads(pathlib.Path("zntrack.json").read_text())
        except FileNotFoundError:
            zntrack_dict = {}

        if instance.name not in zntrack_dict:
            zntrack_dict[instance.name] = {}
        zntrack_dict[instance.name][self.name] = instance.__dict__[self.name]
        # use the __dict__ to avoid the nwd replacement
        pathlib.Path("zntrack.json").write_text(
            json.dumps(zntrack_dict, indent=4, cls=encoder)
        )
