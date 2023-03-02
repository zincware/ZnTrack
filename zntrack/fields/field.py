import abc
import typing

import zninit

from zntrack.core.node import Node


class Field(zninit.Descriptor, abc.ABC):
    """A field for a Node.

    This class handles all the file I/O for the given field.
    """

    @abc.abstractmethod
    def save(self, instance: Node):
        """Save the field to disk."""
        raise NotImplementedError

    @abc.abstractmethod
    def load(self, instance: Node):
        """Load the field from disk."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_stage_add_argument(self, instance: Node) -> typing.List[tuple]:
        """Get the dvc stage add argument for this field."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_affected_files(self, instance: Node) -> list:
        """Get the files affected by this field."""
        raise NotImplementedError
