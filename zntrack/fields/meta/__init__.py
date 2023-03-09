"""Additional fields that are neither dvc/zn i/o fields."""
import pathlib
import typing

import yaml

from zntrack.fields.field import Field, FieldGroup
from zntrack.utils import file_io

if typing.TYPE_CHECKING:
    from zntrack import Node


class Text(Field):
    """A metadata field."""

    dvc_option: str = None
    group = FieldGroup.PARAMETER

    def get_affected_files(self, instance) -> list:
        """Get the params.yaml file."""
        return []

    def save(self, instance):
        """Save the field to disk."""
        file_io.update_meta(
            file=pathlib.Path("dvc.yaml"),
            node_name=instance.name,
            data={self.name: getattr(instance, self.name)},
        )

    def get_data(self, instance: "Node") -> any:
        """Get the value of the field from the file."""
        dvc_dict = yaml.safe_load(instance.state.get_file_system().read_text("dvc.yaml"))
        return dvc_dict["stages"][instance.name]["meta"].get(self.name, None)

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        return []
