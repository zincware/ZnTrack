"""Field with automatic serialization and deserialization."""
import dataclasses
import json
import logging
import pathlib
import typing

import pandas as pd
import yaml
import znflow
import zninit
import znjson

from zntrack.fields.field import Field
from zntrack.utils import NodeStatusResults

if typing.TYPE_CHECKING:
    from zntrack import Node
log = logging.getLogger(__name__)


class ConnectionConverter(znjson.ConverterBase):
    """Convert a znflow.Connection object to dict and back."""

    level = 100
    representation = "znflow.Connection"
    instance = znflow.Connection

    def encode(self, obj: znflow.Connection) -> dict:
        """Convert the znflow.Connection object to dict."""
        return dataclasses.asdict(obj)

    def decode(self, value: str) -> znflow.Connection:
        """Create znflow.Connection object from dict."""
        return znflow.Connection(**value)


class Params(Field):
    """A parameter field."""

    dvc_option: str = "params"

    def get_affected_files(self, instance) -> list:
        """Get the params.yaml file."""
        return ["params.yaml"]

    def save(self, instance: "Node"):
        """Save the field to disk."""
        if instance.state.loaded:
            return  # Don't save if the node is loaded from disk
        file = self.get_affected_files(instance)[0]
        try:
            params_dict = yaml.safe_load(pathlib.Path(file).read_text())
        except FileNotFoundError:
            params_dict = {instance.name: {}}

        if instance.name not in params_dict:
            params_dict[instance.name] = {}

        params_dict[instance.name][self.name] = getattr(instance, self.name)
        params_dict = json.loads(json.dumps(params_dict, cls=znjson.ZnEncoder))
        pathlib.Path("params.yaml").write_text(yaml.safe_dump(params_dict, indent=4))

    def load(self, instance: "Node"):
        """Load the field from disk."""
        file = self.get_affected_files(instance)[0]
        params_dict = yaml.safe_load(instance.state.get_file_system().read_text(file))
        value = params_dict[instance.name].get(self.name, None)
        value = json.loads(json.dumps(value), cls=znjson.ZnDecoder)
        instance.__dict__[self.name] = value

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        file = self.get_affected_files(instance)[0]
        return [(f"--{self.dvc_option}", f"{file}:{instance.name}")]


class Output(Field):
    """A field that is saved to disk."""

    def __init__(self, dvc_option: str, **kwargs):
        """Create a new Output field."""
        self.dvc_option = dvc_option
        super().__init__(**kwargs)

    def get_affected_files(self, instance) -> list:
        """Get the path of the file in the node directory."""
        return [instance.nwd / f"{self.name}.json"]

    def save(self, instance: "Node"):
        """Save the field to disk."""
        if not instance.state.loaded:
            # Only save if the node has been loaded
            return
        instance.nwd.mkdir(exist_ok=True, parents=True)
        file = self.get_affected_files(instance)[0]
        file.write_text(
            json.dumps(getattr(instance, self.name), cls=znjson.ZnEncoder, indent=4)
        )

    def load(self, instance: "Node"):
        """Load the field from disk."""
        file = self.get_affected_files(instance)[0]
        try:
            value = json.loads(
                instance.state.get_file_system().read_text(file.as_posix()),
                cls=znjson.ZnDecoder,
            )
            instance.__dict__[self.name] = value
        except FileNotFoundError:
            instance.state.results = NodeStatusResults.UNKNOWN

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        file = self.get_affected_files(instance)[0]
        return [(f"--{self.dvc_option}", file.as_posix())]


class Plots(Field):
    """A field that is saved to disk."""

    dvc_option: str = "plots"

    def get_affected_files(self, instance) -> list:
        """Get the path of the file in the node directory."""
        return [instance.nwd / f"{self.name}.csv"]

    def save(self, instance: "Node"):
        """Save the field to disk."""
        if not instance.state.loaded:
            # Only save if the node has been loaded
            return
        instance.nwd.mkdir(exist_ok=True, parents=True)
        file = self.get_affected_files(instance)[0]

        value: pd.DataFrame = getattr(instance, self.name)
        value.to_csv(file)

    def load(self, instance: "Node"):
        """Load the field from disk."""
        file = self.get_affected_files(instance)[0]
        try:
            value = pd.read_csv(instance.state.get_file_system().open(file.as_posix()))
            instance.__dict__[self.name] = value
        except FileNotFoundError:
            instance.state.results = NodeStatusResults.UNKNOWN

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        file = self.get_affected_files(instance)[0]
        return [(f"--{self.dvc_option}", file.as_posix())]


_default = object()


class Dependency(Field):
    """A dependency field."""

    dvc_option = "deps"

    def __init__(self, default=_default):
        """Create a new dependency field.

        A `zn.deps` does not support default values.
        To build a dependency graph, the values must be passed at runtime.
        """
        if default is _default:
            super().__init__()
        elif default is None:
            super().__init__(default=default)
        else:
            raise ValueError(
                "A dependency field does not support default dependencies. You can only"
                " use 'None' to declare this an optional dependency"
                f"and not {default}."
            )

    def get_affected_files(self, instance) -> list:
        """Get the affected files of the respective Nodes."""
        files = []

        value = getattr(instance, self.name)

        if not isinstance(value, (list, tuple)):
            value = [value]

        for node in value:
            if node is None:
                continue
            if isinstance(node, znflow.Connection):
                node = node.instance
            for field in zninit.get_descriptors(Field, self=node):
                if field.dvc_option in ["params", "deps"]:
                    # We do not want to depend on parameter files or
                    # recursively on dependencies.
                    continue
                files.extend(field.get_affected_files(node))
                log.debug(f"Found field {field} and extended files to {files}")
        return files

    def save(self, instance: "Node"):
        """Save the field to disk."""
        if instance.state.loaded:
            # Only save if the node has been loaded
            return
        self._write_value_to_config(
            instance,
            encoder=znjson.ZnEncoder.from_converters(
                [ConnectionConverter], add_default=True
            ),
        )

    def load(self, instance: "Node"):
        """Load the field from disk."""
        zntrack_dict = json.loads(
            instance.state.get_file_system().read_text("zntrack.json"),
        )
        value = zntrack_dict[instance.name][self.name]

        def update_key_val(values):
            """Update the keys of the dictionary to the current state of the node.

            If the Nodes dependecy are the default values,
            it will set them to the current Node.
            """
            if isinstance(values, (list, tuple)):
                return [update_key_val(v) for v in values]
            if isinstance(values, dict):
                for key, val in values.items():
                    if key == "rev" and val is None:
                        values[key] = instance.state.rev
                    if key == "origin" and val is None:
                        values[key] = instance.state.origin
                    if isinstance(val, dict):
                        update_key_val(val)
                return values

        value = update_key_val(value)

        value = json.loads(
            json.dumps(value),
            cls=znjson.ZnDecoder.from_converters(ConnectionConverter, add_default=True),
        )

        # Up until here we have connection objects. Now we need to resolve them to Nodes.
        # The Nodes, as in 'connection.instance' are already loaded by the ZnDecoder.
        instance.__dict__[self.name] = znflow.graph._UpdateConnectors()(value)

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        return [
            (f"--{self.dvc_option}", pathlib.Path(file).as_posix())
            for file in self.get_affected_files(instance)
        ]


def params(*args, **kwargs) -> Params:
    """Create a params field."""
    return Params(*args, **kwargs)


def deps(*args, **kwargs) -> Dependency:
    """Create a dependency field."""
    return Dependency(*args, **kwargs)


def outs() -> Output:
    """Create an output field."""
    return Output(dvc_option="outs", use_repr=False)


def metrics() -> Output:
    """Create a metrics output field."""
    return Output(dvc_option="metrics")


def plots(*args, **kwargs) -> Plots:
    """Create a metrics output field."""
    return Plots(*args, **kwargs)
