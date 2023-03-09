"""Field with automatic serialization and deserialization."""
import dataclasses
import json
import logging
import pathlib
import typing

import pandas as pd
import yaml
import znflow.utils
import zninit
import znjson

from zntrack.fields.field import Field, LazyField
from zntrack.utils import module_handler, update_key_val

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
        if obj.item is not None:
            raise NotImplementedError("znflow.Connection getitem is not supported yet.")
        return dataclasses.asdict(obj)

    def decode(self, value: str) -> znflow.Connection:
        """Create znflow.Connection object from dict."""
        return znflow.Connection(**value)


class SliceConverter(znjson.ConverterBase):
    """Convert a znflow.Connection object to dict and back."""

    level = 100
    representation = "slice"
    instance = slice

    def encode(self, obj: slice) -> dict:
        """Convert the znflow.Connection object to dict."""
        return {"start": obj.start, "stop": obj.stop, "step": obj.step}

    def decode(self, value: dict) -> znflow.Connection:
        """Create znflow.Connection object from dict."""
        return slice(*value.values())


znjson.config.register(SliceConverter)


class Params(Field):
    """A parameter field.

    Parameters
    ----------
    dvc_option: str
        The DVC option to use. Default is "params".
    """

    dvc_option: str = "params"

    def get_affected_files(self, instance: "Node") -> list:
        """Get the list of files affected by this field.

        Returns
        -------
        list
            A list of file paths.
        """
        return ["params.yaml"]

    def save(self, instance: "Node"):
        """Save the field to disk.

        Parameters
        ----------
        instance : Node
            The node instance associated with this field.
        """
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

        with open(file, "w") as f:
            yaml.safe_dump(params_dict, f, indent=4)

    def _get_value_from_file(self, instance: "Node") -> any:
        file = self.get_affected_files(instance)[0]
        params_dict = yaml.safe_load(instance.state.get_file_system().read_text(file))
        value = params_dict[instance.name].get(self.name, None)
        return json.loads(json.dumps(value), cls=znjson.ZnDecoder)

    def get_stage_add_argument(self, instance: "Node") -> typing.List[tuple]:
        """Get the DVC stage add argument for this field.

        Parameters
        ----------
        instance : Node
            The node instance associated with this field.

        Returns
        -------
        list
            A list of tuples containing the DVC option and the file path.
        """
        file = self.get_affected_files(instance)[0]
        return [(f"--{self.dvc_option}", f"{file}:{instance.name}")]


class Output(LazyField):
    """A field that is saved to disk."""

    def __init__(self, dvc_option: str, **kwargs):
        """Create a new Output field.

        Parameters
        ----------
        dvc_option : str
            The DVC option used to specify the output file.
        **kwargs
            Additional arguments to pass to the parent constructor.
        """
        self.dvc_option = dvc_option
        super().__init__(**kwargs)

    def get_affected_files(self, instance) -> list:
        """Get the path of the file in the node directory.

        Parameters
        ----------
        instance : Node
            The node instance.

        Returns
        -------
        list
            A list containing the path of the file.
        """
        return [instance.nwd / f"{self.name}.json"]

    def save(self, instance: "Node"):
        """Save the field to disk.

        Parameters
        ----------
        instance : Node
            The node instance.
        """
        try:
            value = getattr(instance, self.name)
        except AttributeError:
            return

        instance.nwd.mkdir(exist_ok=True, parents=True)
        file = self.get_affected_files(instance)[0]
        file.write_text(json.dumps(value, cls=znjson.ZnEncoder, indent=4))

    def _get_value_from_file(self, instance: "Node") -> any:
        file = self.get_affected_files(instance)[0]
        return json.loads(
            instance.state.get_file_system().read_text(file.as_posix()),
            cls=znjson.ZnDecoder,
        )

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the DVC command for this field.

        Parameters
        ----------
        instance : Node
            The node instance.

        Returns
        -------
        list
            A list containing the DVC command for this field.
        """
        file = self.get_affected_files(instance)[0]
        return [(f"--{self.dvc_option}", file.as_posix())]


class Plots(LazyField):
    """A field that is saved to disk."""

    dvc_option: str = "plots"

    def get_affected_files(self, instance) -> list:
        """Get the path of the file in the node directory."""
        return [instance.nwd / f"{self.name}.csv"]

    def save(self, instance: "Node"):
        """Save the field to disk."""
        try:
            value: pd.DataFrame = getattr(instance, self.name)
        except AttributeError:
            return

        instance.nwd.mkdir(exist_ok=True, parents=True)
        file = self.get_affected_files(instance)[0]
        value.to_csv(file)

    def _get_value_from_file(self, instance: "Node") -> any:
        file = self.get_affected_files(instance)[0]
        return pd.read_csv(
            instance.state.get_file_system().open(file.as_posix()), index_col=0
        )

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        file = self.get_affected_files(instance)[0]
        return [(f"--{self.dvc_option}", file.as_posix())]


_default = object()


class Dependency(LazyField):
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
        try:
            value = instance.__dict__[self.name]
        except KeyError:
            return

        self._write_value_to_config(
            value,
            instance,
            encoder=znjson.ZnEncoder.from_converters(
                [ConnectionConverter], add_default=True
            ),
        )

    def _get_value_from_file(self, instance: "Node") -> any:
        zntrack_dict = json.loads(
            instance.state.get_file_system().read_text("zntrack.json"),
        )
        value = zntrack_dict[instance.name][self.name]

        value = update_key_val(value, instance=instance)

        value = json.loads(
            json.dumps(value),
            cls=znjson.ZnDecoder.from_converters(ConnectionConverter, add_default=True),
        )

        # Up until here we have connection objects. Now we need
        # to resolve them to Nodes. The Nodes, as in 'connection.instance'
        #  are already loaded by the ZnDecoder.
        return znflow.graph._UpdateConnectors()(value)

    def get_stage_add_argument(self, instance) -> typing.List[tuple]:
        """Get the dvc command for this field."""
        return [
            (f"--{self.dvc_option}", pathlib.Path(file).as_posix())
            for file in self.get_affected_files(instance)
        ]


class _SaveNodes(znflow.utils.IterableHandler):
    def default(self, value, **kwargs):
        name = kwargs["name"]
        if hasattr(value, "save"):
            value.name = name
            value.save()
        return value


class NodeFiled(Dependency):
    """Add another Node as a field.

    The other Node will provide its parameters and methods to be used.
    From a graph standpoint, it will add these parameters and methods to the Node
    it is attached to.
    The Node will not execute its run method or save any results to disk.
    """

    def __set__(self, instance, value):
        """Disbale the _graph_ in the value 'Node'."""
        if hasattr(value, "_graph_"):
            value._graph_ = None
        else:
            raise TypeError(f"The value must be a Node and not {value}.")
        return super().__set__(instance, value)

    def get_node_name(self, instance) -> str:
        """Get the name of the other Node."""
        return f"{instance.name}_{self.name}"

    def save(self, instance: "Node"):
        """Save the Node parameters to disk."""
        value = instance.__dict__[self.name]
        _SaveNodes()(value, name=self.get_node_name(instance))
        super().save(instance)

    def get_optional_dvc_cmd(self, instance: "Node") -> typing.List[tuple]:
        """Get the dvc command for this field."""
        name = self.get_node_name(instance)
        node = instance.__dict__[self.name]
        if not isinstance(node, znflow.Node):
            raise TypeError(f"The value must be a Node and not {node}.")
        module = module_handler(node.__class__)
        return [
            "stage",
            "add",
            "--name",
            name,
            "--outs",
            f"nodes/{name}/hash",
            f"zntrack run {module}.{node.__class__.__name__} --name {name} --hash-only",
        ]

    def get_affected_files(self, instance: "Node") -> list:
        """Get the files affected by this field."""
        name = self.get_node_name(instance)
        return [pathlib.Path(f"nodes/{name}/hash")]


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


def nodes(*args, **kwargs) -> NodeFiled:
    """Create a node field."""
    return NodeFiled(*args, **kwargs)
