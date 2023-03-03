import dataclasses
import importlib
import json
import pathlib
import typing

import yaml
import znflow
import zninit
import znjson

from zntrack.core.node import Node, NodeStatusResults
from zntrack.fields.field import Field
from zntrack.utils import module_handler


class ConnectionConverter(znjson.ConverterBase):
    level = 100
    representation = "znflow.Connection"
    instance = znflow.Connection

    def encode(self, obj: znflow.Connection) -> dict:
        """Convert the znflow.Connection object to dict"""
        return dataclasses.asdict(obj)

    def decode(self, value: str) -> znflow.Connection:
        """Create znflow.Connection object from dict"""
        return znflow.Connection(**value)


class NodeConverter(znjson.ConverterBase):
    level = 100
    representation = "zntrack.core.node.Node"
    instance = Node

    def encode(self, obj: Node) -> str:
        """Convert the datetime object to str / isoformat"""
        # TODO rev / origin
        return {
            "module": module_handler(obj),
            "cls": obj.__class__.__name__,
            "name": obj.name,
        }

    def decode(self, value: str) -> Node:
        """Create datetime object from str / isoformat"""
        module = importlib.import_module(value["module"])
        cls = getattr(module, value["cls"])
        return cls.from_rev(value["name"])


class Params(Field):
    dvc_option: str = "params"

    def get_affected_files(self, instance) -> list:
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
    def __init__(self, dvc_option: str, **kwargs):
        self.dvc_option = dvc_option
        super().__init__(default=None, **kwargs)

    def get_affected_files(self, instance) -> list:
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


class Dependency(Field):
    def get_affected_files(self, instance) -> list:
        """Get the affected files of the respective Nodes."""
        files = []

        value = getattr(instance, self.name)
        if isinstance(value, znflow.Connection):
            # TODO, recursive
            value = value.instance
            print(f"Found connection {value}")

        for field in zninit.get_descriptors(Field, self=value):
            if field.dvc_option == "params":
                # We do not want to depend on parameter files.
                continue
            files.extend(field.get_affected_files(value))
            print(f"Found field {field} and extended files to {files}")
        return files

    def save(self, instance: Node):
        """Save the field to disk."""
        if instance.state.loaded:
            # Only save if the node has been loaded
            return
        try:
            zntrack_dict = json.loads(pathlib.Path("zntrack.json").read_text())
        except FileNotFoundError:
            zntrack_dict = {}

        if instance.name not in zntrack_dict:
            zntrack_dict[instance.name] = {}
        zntrack_dict[instance.name][self.name] = getattr(instance, self.name)
        pathlib.Path("zntrack.json").write_text(
            json.dumps(
                zntrack_dict,
                indent=4,
                cls=znjson.ZnEncoder.from_converters(
                    [ConnectionConverter, NodeConverter]
                ),
            )
        )

    def load(self, instance: Node):
        """Load the field from disk."""
        zntrack_dict = json.loads(
            instance.state.get_file_system().read_text("zntrack.json"),
        )
        value = json.loads(
            json.dumps(zntrack_dict[instance.name][self.name]),
            cls=znjson.ZnDecoder.from_converters([ConnectionConverter, NodeConverter]),
        )

        if isinstance(value, znflow.Connection):
            # TODO, recursive
            # If we load the Node, we don't want to load the connection but the instance / result
            value = value.result

        instance.__dict__[self.name] = value

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        return [
            (f"--deps", pathlib.Path(file).as_posix())
            for file in self.get_affected_files(instance)
        ]


def params(*args, **kwargs) -> Params:
    return Params(*args, **kwargs)


def deps(*args, **kwargs) -> Dependency:
    return Dependency(*args, **kwargs)


def outs() -> Output:
    return Output(dvc_option="outs", use_repr=False)


def metrics() -> Output:
    return Output(dvc_option="metrics")
