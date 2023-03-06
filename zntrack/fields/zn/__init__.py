"""Field with automatic serialization and deserialization."""
import dataclasses
import json
import pathlib
import typing

import pandas as pd
import yaml
import znflow
import zninit
import znjson

from zntrack.core.node import Node, NodeIdentifier, NodeStatusResults
from zntrack.fields.field import Field


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


class NodeConverter(znjson.ConverterBase):
    """A converter for the Node class."""

    level = 100
    representation = "zntrack.Node"
    instance = Node

    def encode(self, obj: Node) -> dict:
        """Convert the Node object to dict."""
        node_identifier = NodeIdentifier.from_node(obj)
        if node_identifier.rev != "HEAD":
            raise NotImplementedError(
                "Dependencies to other revisions are not supported yet"
            )

        return dataclasses.asdict(node_identifier)

    def decode(self, value: dict) -> Node:
        """Create Node object from dict."""
        return NodeIdentifier(**value).get_node()


class Params(Field):
    """A parameter field."""

    dvc_option: str = "params"

    def get_affected_files(self, instance) -> list:
        """Get the params.yaml file."""
        return ["params.yaml"]

    def save(self, instance: Node):
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
        pathlib.Path("params.yaml").write_text(yaml.safe_dump(params_dict, indent=4))

    def load(self, instance: Node):
        """Load the field from disk."""
        file = self.get_affected_files(instance)[0]
        params_dict = yaml.safe_load(instance.state.get_file_system().read_text(file))
        instance.__dict__[self.name] = params_dict[instance.name].get(self.name, None)

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        file = self.get_affected_files(instance)[0]
        return [(f"--{self.dvc_option}", f"{file}:{instance.name}")]


class Output(Field):
    """A field that is saved to disk."""

    def __init__(self, dvc_option: str, **kwargs):
        """Create a new Output field."""
        self.dvc_option = dvc_option
        super().__init__(default=None, **kwargs)

    def get_affected_files(self, instance) -> list:
        """Get the path of the file in the node directory."""
        return [instance.nwd / f"{self.name}.json"]

    def save(self, instance: Node):
        """Save the field to disk."""
        if not instance.state.loaded:
            # Only save if the node has been loaded
            return
        instance.nwd.mkdir(exist_ok=True, parents=True)
        file = self.get_affected_files(instance)[0]
        file.write_text(
            json.dumps(getattr(instance, self.name), cls=znjson.ZnEncoder, indent=4)
        )

    def load(self, instance: Node):
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

    def save(self, instance: Node):
        """Save the field to disk."""
        if not instance.state.loaded:
            # Only save if the node has been loaded
            return
        instance.nwd.mkdir(exist_ok=True, parents=True)
        file = self.get_affected_files(instance)[0]

        value: pd.DataFrame = getattr(instance, self.name)
        value.to_csv(file)

    def load(self, instance: Node):
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

    def __init__(self, default=_default):
        """Create a new dependency field.

        A `zn.deps` does not support default values.
        To build a dependency graph, the values must be passed at runtime.
        """
        super().__init__()
        if default not in (_default, None):
            raise ValueError(
                "A dependency field does not support default dependencies. You can only"
                " use 'None' to declare this an optional dependency."
            )

    def get_affected_files(self, instance) -> list:
        """Get the affected files of the respective Nodes."""
        files = []

        value = getattr(instance, self.name)

        if not isinstance(value, (list, tuple)):
            value = [value]

        for node in value:
            if isinstance(node, znflow.Connection):
                node = node.instance
            for field in zninit.get_descriptors(Field, self=node):
                if field.dvc_option == "params":
                    # We do not want to depend on parameter files.
                    continue
                files.extend(field.get_affected_files(node))
                print(f"Found field {field} and extended files to {files}")
        return files

    def save(self, instance: Node):
        """Save the field to disk."""
        if instance.state.loaded:
            # Only save if the node has been loaded
            return
        self._write_value_to_config(
            instance,
            encoder=znjson.ZnEncoder.from_converters(
                [ConnectionConverter, NodeConverter]
            ),
        )

    def load(self, instance: Node):
        """Load the field from disk."""
        value = self._get_value_from_config(
            instance,
            decoder=znjson.ZnDecoder.from_converters(
                [ConnectionConverter, NodeConverter]
            ),
        )

        instance.__dict__[self.name] = znflow.graph._UpdateConnectors()(value)

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        return [
            ("--deps", pathlib.Path(file).as_posix())
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
