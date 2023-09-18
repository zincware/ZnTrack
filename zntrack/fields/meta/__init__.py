"""Additional fields that are neither dvc/zn i/o fields."""
import json
import pathlib
import typing

import yaml
import znjson

from zntrack.fields.field import Field, FieldGroup
from zntrack.utils import config, file_io

if typing.TYPE_CHECKING:
    from zntrack import Node


class Text(Field):
    """A metadata field."""

    dvc_option: str = None
    group = FieldGroup.PARAMETER
    use_dvc_yaml: bool = False

    def get_files(self, instance) -> list:
        """Get the params.yaml file."""
        return []

    def save(self, instance):
        """Save the field to disk."""
        value = getattr(instance, self.name)
        if config.files.dvc.exists() and self.use_dvc_yaml:
            file_io.update_meta(
                file=config.files.dvc,
                node_name=instance.name,
                data={self.name: value},
            )
        else:
            # load from zntrack.json
            self._write_value_to_config(value, instance, encoder=znjson.ZnEncoder)

    def get_data(self, instance: "Node") -> any:
        """Get the value of the field from the file."""
        if config.files.dvc.exists() and self.use_dvc_yaml:
            dvc_dict = yaml.safe_load(instance.state.fs.read_text(config.files.dvc))
            return dvc_dict["stages"][instance.name]["meta"].get(self.name, None)
        else:
            # load from zntrack.json
            zntrack_dict = json.loads(
                instance.state.fs.read_text(config.files.zntrack),
            )
            return json.loads(
                json.dumps(zntrack_dict[instance.name][self.name]), cls=znjson.ZnDecoder
            )

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        return []


class Environment(Field):
    """Environment variables to export."""

    dvc_option: str = None
    group = FieldGroup.PARAMETER

    def __init__(self, *args, is_parameter: bool = False, **kwargs):
        """Initialize the field."""
        self.is_parameter = is_parameter
        super().__init__(*args, **kwargs)

    def get_files(self, instance) -> list:
        """There are no affect files."""
        return []

    def save(self, instance):
        """Save the field to disk."""
        file = pathlib.Path("env.yaml")
        try:
            context = yaml.safe_load(file.read_text())
        except FileNotFoundError:
            context = {}

        stages = context.get("stages", {})
        # TODO: when to reset the environment variables?

        node_context = stages.get(instance.name, {})
        value = getattr(instance, self.name)
        if isinstance(value, (str, dict)):
            node_context[self.name] = value
            stages[instance.name] = node_context
        elif value is None:
            return
        else:
            raise ValueError(
                f"Environment value must be a string or dict, not {type(value)}"
            )

        context["stages"] = stages
        file.write_text(yaml.safe_dump(context))

    def get_data(self, instance: "Node") -> any:
        """Get the value of the field from the file."""
        env_dict = yaml.safe_load(instance.state.fs.read_text("env.yaml"))
        return env_dict.get("stages", {}).get(instance.name, {}).get(self.name, None)

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        if self.is_parameter:
            return [("--params", f"env.yaml:stages.{instance.name}.{self.name}")]
        return []
