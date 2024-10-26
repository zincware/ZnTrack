import dataclasses
import importlib
import pathlib
import subprocess
import typing as t
import warnings

import yaml
import znflow
import znjson

from zntrack.add import DVCImportPath
from zntrack.config import (
    PARAMS_FILE_PATH,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)

from .node import Node
from .utils import module_handler


class DataclassContainer:
    def __init__(self, cls):
        self.cls = cls

    def get_with_params(self, node_name, attr_name, index: int | None = None):
        """Get an instance of the dataclass with the parameters from the params file.

        Attributes
        ----------
        node_name : str
            The name of the node.
        attr_name : str
            The name of the attribute.
        index : int | None
            The index in the parameter file, if the node attribute
            is a list of dataclasses. None if a single dataclass.

        """
        all_params = yaml.safe_load(PARAMS_FILE_PATH.read_text())
        if index is not None:
            dc_params = all_params[node_name][attr_name][index]
        else:
            dc_params = all_params[node_name][attr_name]
        dc_params.pop("_cls", None)
        return self.cls(**dc_params)


def _enforce_str_list(content) -> list[str]:
    if isinstance(content, (str, pathlib.Path)):
        return [pathlib.Path(content).as_posix()]
    elif isinstance(content, (list, tuple)):
        return [pathlib.Path(x).as_posix() for x in content]
    else:
        raise ValueError(f"found unsupported content type '{content}'")


class NodeDict(t.TypedDict):
    module: str
    name: str
    cls: str
    remote: t.Optional[t.Any]
    rev: t.Optional[t.Any]


class NodeConverter(znjson.ConverterBase):
    level = 100
    instance = Node
    representation = "zntrack.Node"

    def encode(self, obj: Node) -> NodeDict:
        return {
            "module": module_handler(obj),
            "name": obj.name,
            "cls": obj.__class__.__name__,
            "remote": obj.state.remote,
            "rev": obj.state.rev,
        }

    def decode(self, s: dict) -> Node:
        module = importlib.import_module(s["module"])
        cls = getattr(module, s["cls"])
        return cls.from_rev(name=s["name"], remote=s["remote"], rev=s["rev"])


class ConnectionConverter(znjson.ConverterBase):
    """Convert a znflow.Connection object to dict and back."""

    level = 100
    representation = "znflow.Connection"
    instance = znflow.Connection

    def encode(self, obj: znflow.Connection) -> dict:
        """Convert the znflow.Connection object to dict."""
        if obj.item is not None:
            raise NotImplementedError("znflow.Connection getitem is not supported yet.")
        # Can not use `dataclasses.asdict` because it automatically converts nested dataclasses to dict.
        return {
            "instance": obj.instance,
            "attribute": obj.attribute,
            "item": obj.item,
        }

    def decode(self, value: dict) -> znflow.Connection:
        """Create znflow.Connection object from dict."""
        return znflow.Connection(**value)


class CombinedConnectionsConverter(znjson.ConverterBase):
    """Convert a znflow.Connection object to dict and back."""

    level = 100
    representation = "znflow.CombinedConnections"
    instance = znflow.CombinedConnections

    def encode(self, obj: znflow.CombinedConnections) -> dict:
        """Convert the znflow.Connection object to dict."""
        if obj.item is not None:
            raise NotImplementedError(
                "znflow.CombinedConnections getitem is not supported yet."
            )
        return {
            "connections": obj.connections,
            "item": obj.item,
        }

    def decode(self, value: dict) -> znflow.CombinedConnections:
        """Create znflow.Connection object from dict."""
        return znflow.CombinedConnections(**value)


def node_to_output_paths(node: Node, attribute: str) -> t.List[str]:
    """Get all output paths for a node."""
    # TODO: this should be a part of the DVCPlugin!
    if not isinstance(node, Node):
        raise ValueError(f"Expected a Node object, got {type(node)}")
    import_path = None
    if node._external_:
        # DODO: use the dvc_stage hash instead!
        # try use the one including the outputs
        import_path = pathlib.Path(
            "external", node.state.get_stage_hash(include_outs=True)[:32]
        )
        import_path.mkdir(exist_ok=True, parents=True)
        # we need to make the parent directory of the output
        # that directory is probably best described by using the node.name
        # of the node that depends on the import?
        # or we use a hash from commit / node name / repo path <-- only validate answer!
        # we want to run dvc import remote get_path(node, "attribute") --rev rev --out /.../get_path(node, "attribute").name
        # use --no-download option while building
        # check how dvc repro or paraffin would download files? Do we want the user to force download?
        # have zntrack.Path(path, remote, rev, is_dvc_tracked, is_db) to use dvc import-url / import-db in the graph
        # return []
        # raise NotImplementedError
    if attribute is None:
        fields = dataclasses.fields(node)
    else:
        try:
            fields = [node.state.get_field(attribute)]
        except AttributeError:
            # if you e.g. pass a property, we can not
            # determine what data is used and need
            # to assume all fields are used.
            # TODO: tests
            # TODO: have a custom decorator which defines the fields used?
            fields = dataclasses.fields(node)
    paths = []
    for field in fields:
        option_type = field.metadata.get(ZNTRACK_OPTION)

        if any(
            option_type is x
            for x in [
                ZnTrackOptionEnum.PARAMS,
                ZnTrackOptionEnum.PARAMS,
                ZnTrackOptionEnum.DEPS,
                ZnTrackOptionEnum.DEPS_PATH,
                None,
            ]
        ):
            continue
        if node._external_:
            warnings.warn("External nodes are currently always loaded dynamically.")
            continue
        if field.metadata.get(ZNTRACK_INDEPENDENT_OUTPUT_TYPE) == True:
            paths.append((node.nwd / "node-meta.json").as_posix())
            if node._external_:
                raise NotImplementedError
                # paths.append((import_path / "node-meta.json").as_posix())
        if option_type == ZnTrackOptionEnum.OUTS:
            paths.append((node.nwd / f"{field.name}.json").as_posix())
        elif option_type == ZnTrackOptionEnum.PLOTS:
            paths.append((node.nwd / f"{field.name}.csv").as_posix())
        elif option_type == ZnTrackOptionEnum.METRICS:
            paths.append((node.nwd / f"{field.name}.json").as_posix())
        elif option_type == ZnTrackOptionEnum.OUTS_PATH:
            paths.extend(_enforce_str_list(getattr(node, field.name)))
        elif option_type == ZnTrackOptionEnum.PLOTS_PATH:
            paths.extend(_enforce_str_list(getattr(node, field.name)))
        elif option_type == ZnTrackOptionEnum.METRICS_PATH:
            paths.extend(_enforce_str_list(getattr(node, field.name)))

    if len(paths) == 0:
        if node._external_:
            node_meta_path = import_path / "node-meta.json"
            if not node_meta_path.exists():
                cmd = [
                    "dvc",
                    "import",
                    node.state.remote,
                    (node.nwd / "node-meta.json").as_posix(),
                ]
                if node.state.rev is not None:
                    cmd.extend(["--rev", node.state.rev])
                cmd.append("--no-download")  # consider using --no-exec
                cmd.extend(["--out", node_meta_path.as_posix()])
                subprocess.check_call(cmd)
            paths.append(node_meta_path.as_posix())
        else:
            # for nodes with no outputs, we rely on 'node-meta.json'
            paths.append((node.nwd / "node-meta.json").as_posix())

    return paths


class DataclassConverter(znjson.ConverterBase):
    """Convert a python dataclass object to dict and back.

    This converter does not return an instance, but
    only the class inside a DataclassContainer.
    Saving the values must be done separately.

    Attributes
    ----------
    representation: str
        representation inside the dict for deserialization.
    level: int
        The level in which the encoding should be applied. A higher number means it will
        try this first. E.g. test small numpy conversion before pickle
        first.

    """

    level = 20
    representation = "@dataclasses.dataclass"

    def encode(self, obj: object) -> dict:
        """Convert the znflow.Connection object to dict."""
        module = module_handler(obj)
        cls = obj.__class__.__name__

        return {
            "module": module,
            "cls": cls,
        }

    def decode(self, value: dict) -> DataclassContainer:
        """Create znflow.Connection object from dict."""
        module = importlib.import_module(value["module"])
        cls = getattr(module, value["cls"])
        return DataclassContainer(cls)

    def __eq__(self, other) -> bool:
        if dataclasses.is_dataclass(other) and not isinstance(
            other, (Node, znflow.Connection, znflow.CombinedConnections)
        ):
            return True
        return False


class DVCImportPathConverter(znjson.ConverterBase):
    """Convert a DVCImportPath object to to pathlib.

    We do not want to store the information about the DVCImportPath
    as this is handled in the "path.dvc" file.
    Thus, we just make use of the pathlib.Path representation.
    """

    level = 100
    instance = DVCImportPath
    representation = "pathlib.Path"

    def encode(self, obj: DVCImportPath) -> str:
        return obj.path.as_posix()

    def decode(self, value: str) -> None:
        raise NotImplementedError("DVCImportPath is converted to pathlib.Path.")
