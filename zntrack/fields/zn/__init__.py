import json
import pathlib
import typing

import yaml
import znjson

from zntrack.core.node import Node, NodeStatusResults
from zntrack.fields.field import Field


class Params(Field):
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

        params_dict[instance.name][self.name] = getattr(instance, self.name)
        pathlib.Path("params.yaml").write_text(yaml.safe_dump(params_dict, indent=4))

    def load(self, instance: Node):
        """Load the field from disk."""
        file = self.get_affected_files(instance)[0]
        params_dict = yaml.safe_load(instance.state.get_file_system().read_text(file))
        instance.__dict__[self.name] = params_dict[instance.name][self.name]

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        file = self.get_affected_files(instance)[0]
        return [("--params", f"{file}:{instance.name}")]


class Output(Field):
    def __init__(self, dvc_option: str):
        self.dvc_option = dvc_option
        super().__init__(default=None)

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


def params(*args, **kwargs) -> Params:
    return Params(*args, **kwargs)


def outs() -> Output:
    return Output(dvc_option="outs")

def metrics() -> Output:
    return Output(dvc_option="metrics")
