"""Dependency field."""

import json
import logging
import pathlib
import typing as t

import znflow
import zninit
import znjson
from znflow import handler

from zntrack import exceptions
from zntrack.fields.field import DataIsLazyError, Field, FieldGroup, LazyField
from zntrack.fields.zn import (
    CombinedConnectionsConverter,
    ConnectionConverter,
    _default,
    _get_all_connections_and_instances,
)
from zntrack.utils import config, update_key_val

log = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    from zntrack import Node


class _Dependency(LazyField):
    """A dependency field."""

    dvc_option = "deps"
    group = FieldGroup.PARAMETER

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

    def _handle_files_on_graph(self, instance, entries) -> t.List[pathlib.Path]:
        nodes = []
        files = []
        for entry in entries:
            if isinstance(entry, (znflow.CombinedConnections, znflow.Connection)):
                nodes.extend(_get_all_connections_and_instances(entry))
            else:
                nodes.append(entry)

        for node in nodes:
            node: Node
            if node is None:
                continue
            if node._external_:
                from zntrack.utils import run_dvc_cmd

                # TODO save these files in a specific directory called `external`
                # TODO the `dvc import cmd` should not run here but rather be a stage?

                deps_file = pathlib.Path("external", f"{node.uuid}.json")
                deps_file.parent.mkdir(exist_ok=True, parents=True)

                # zntrack run node.name --external \
                # --remote node.state.remote --rev node.state.rev

                # when combining with zn.nodes this should be used
                # dvc stage add <name> --params params.yaml:<name>
                # --outs nodes/<name>/node-meta.json zntrack run <name> --external

                cmd = [
                    "import",
                    node.state.remote if node.state.remote is not None else ".",
                    (node.nwd / "node-meta.json").as_posix(),
                    "-o",
                    deps_file.as_posix(),
                ]
                if node.state.rev is not None:
                    cmd.extend(["--rev", node.state.rev])
                # TODO how can we test, that the loaded file truly is the correct one?
                if not deps_file.exists():
                    run_dvc_cmd(cmd)
                files.append(deps_file.as_posix())
                # dvc import node-meta.json + add as dependency file
                continue
            # if node.state.rev is not None or node.state.remote is not None:
            #     # TODO if the Node has a `rev` or `remote` attribute, we need to
            #     #  get the UUID file of the respective Node through node.state.fs.open
            #     # save that somewhere (can't use NWD, because we can now have multiple
            #     # nodes with the same name...)
            #     # and make the uuid a dependency of the node.
            #     continue
            files.append(node.nwd / "node-meta.json")
            for field in zninit.get_descriptors(Field, self=node):
                if field.dvc_option in ["params", "deps"]:
                    # We do not want to depend on parameter files or
                    # recursively on dependencies.
                    continue
                files.extend(field.get_files(node))
                log.debug(f"Found field {field} and extended files to {files}")
        return files

    def _handle_files_off_graph(self, instance, entries) -> t.List[pathlib.Path]:
        return []

    def _get_nodes_on_off_graph(self, instance) -> t.Tuple[list, list]:
        """Get the nodes that are on the graph and off the graph.

        Get the values of this descriptor and split them into
        nodes that are on the graph and off the graph.
        These represent `zn.deps` and `zn.nodes` respectively.


        Attributes
        ----------
        instance : Node
            The Node instance.

        Returns
        -------
        on_graph : list
            The nodes that are on the graph.
        off_graph : list
            The nodes that are off the graph.
        """
        values = getattr(instance, self.name)
        # TODO use IterableHandler?

        if isinstance(values, dict):
            values = list(values.values())

        if isinstance(values, tuple):
            values = list(values)

        if not isinstance(values, list):
            values = [values]

        on_graph = []
        off_graph = []
        for entry in values:
            if hasattr(entry, "_graph_"):
                if entry.uuid in instance._graph_:
                    on_graph.append(entry)
                else:
                    entry._graph_ = None
                    off_graph.append(entry)
        return on_graph, off_graph

    def get_files(self, instance) -> list:
        """Get the affected files of the respective Nodes."""
        files = []

        entries_on_graph, entries_off_graph = self._get_nodes_on_off_graph(instance)

        files.extend(self._handle_files_on_graph(instance, entries_on_graph))
        files.extend(self._handle_files_off_graph(instance, entries_off_graph))

        return files

    def save(self, instance: "Node"):
        """Save the dependencies of the Node."""
        try:
            values = self.get_value_except_lazy(instance)
        except DataIsLazyError:
            return

        self._write_value_to_config(
            values,
            instance,
            encoder=znjson.ZnEncoder.from_converters(
                [ConnectionConverter, CombinedConnectionsConverter], add_default=True
            ),
        )

    def get_data(self, instance: "Node") -> any:
        """Get the value of the field from the file."""
        zntrack_dict = json.loads(
            instance.state.fs.read_text(config.files.zntrack),
        )
        value = zntrack_dict[instance.name][self.name]

        value = update_key_val(value, instance=instance)

        value = json.loads(
            json.dumps(value),
            cls=znjson.ZnDecoder.from_converters(
                [ConnectionConverter, CombinedConnectionsConverter], add_default=True
            ),
        )

        # Up until here we have connection objects. Now we need
        # to resolve them to Nodes. The Nodes, as in 'connection.instance'
        #  are already loaded by the ZnDecoder.
        return handler.UpdateConnectors()(value)


class Dependency(LazyField):
    """A dependency field."""

    dvc_option = "deps"
    group = FieldGroup.PARAMETER

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

    def __set__(self, instance, value):
        """Disable the _graph_ in the value 'Node'."""
        if value is None:
            return super().__set__(instance, value)

        for entry in value if isinstance(value, (list, tuple)) else [value]:
            if hasattr(entry, "_graph_"):
                entry._graph_ = None
                if entry.uuid in instance._graph_:
                    raise exceptions.ZnNodesOnGraphError(
                        node=entry, field=self, instance=instance
                    )
            else:
                raise TypeError(f"The value must be a Node and not {entry}.")
        return super().__set__(instance, value)

    def _get_nodes_on_off_graph(self, instance) -> t.Tuple[list, list]:
        """Get the nodes that are on the graph and off the graph.

        Get the values of this descriptor and split them into
        nodes that are on the graph and off the graph.
        These represent `zn.deps` and `zn.nodes` respectively.


        Attributes
        ----------
        instance : Node
            The Node instance.

        Returns
        -------
        on_graph : list
            The nodes that are on the graph.
        off_graph : list
            The nodes that are off the graph.
        """
        values = getattr(instance, self.name)
        # TODO use IterableHandler?

        if isinstance(values, dict):
            values = list(values.values())

        if isinstance(values, tuple):
            values = list(values)

        if not isinstance(values, list):
            values = [values]

        on_graph = []
        off_graph = []
        for entry in values:
            if hasattr(entry, "_graph_"):
                # if entry.uuid in instance._graph_:
                #     on_graph.append(entry)
                # else:
                off_graph.append(entry)
        return on_graph, off_graph

    def get_files(self, instance) -> list:
        """Get the affected files of the respective Nodes."""
        files = []

        value, _ = self._get_nodes_on_off_graph(instance)

        for node in value:
            node: Node
            if node is None:
                continue
            if node._external_:
                from zntrack.utils import run_dvc_cmd

                # TODO save these files in a specific directory called `external`
                # TODO the `dvc import cmd` should not run here but rather be a stage?

                deps_file = pathlib.Path("external", f"{node.uuid}.json")
                deps_file.parent.mkdir(exist_ok=True, parents=True)

                # zntrack run node.name --external \
                # --remote node.state.remote --rev node.state.rev

                # when combining with zn.nodes this should be used
                # dvc stage add <name> --params params.yaml:<name>
                # --outs nodes/<name>/node-meta.json zntrack run <name> --external

                cmd = [
                    "import",
                    node.state.remote if node.state.remote is not None else ".",
                    (node.nwd / "node-meta.json").as_posix(),
                    "-o",
                    deps_file.as_posix(),
                ]
                if node.state.rev is not None:
                    cmd.extend(["--rev", node.state.rev])
                # TODO how can we test, that the loaded file truly is the correct one?
                if not deps_file.exists():
                    run_dvc_cmd(cmd)
                files.append(deps_file.as_posix())
                # dvc import node-meta.json + add as dependency file
                continue
            # if node.state.rev is not None or node.state.remote is not None:
            #     # TODO if the Node has a `rev` or `remote` attribute, we need to
            #     #  get the UUID file of the respective Node through node.state.fs.open
            #     # save that somewhere (can't use NWD, because we can now have multiple
            #     # nodes with the same name...)
            #     # and make the uuid a dependency of the node.
            #     continue
            files.append(node.nwd / "node-meta.json")
            for field in zninit.get_descriptors(Field, self=node):
                if field.dvc_option in ["params", "deps"]:
                    # We do not want to depend on parameter files or
                    # recursively on dependencies.
                    continue
                files.extend(field.get_files(node))
                log.debug(f"Found field {field} and extended files to {files}")
        return files

    def save(self, instance: "Node"):
        """Save the field to disk."""
        try:
            value = self.get_value_except_lazy(instance)
        except DataIsLazyError:
            return

        self._write_value_to_config(
            value,
            instance,
            encoder=znjson.ZnEncoder.from_converters(
                [ConnectionConverter, CombinedConnectionsConverter], add_default=True
            ),
        )

    def get_data(self, instance: "Node") -> any:
        """Get the value of the field from the file."""
        zntrack_dict = json.loads(
            instance.state.fs.read_text(config.files.zntrack),
        )
        value = zntrack_dict[instance.name][self.name]

        value = update_key_val(value, instance=instance)

        value = json.loads(
            json.dumps(value),
            cls=znjson.ZnDecoder.from_converters(
                [ConnectionConverter, CombinedConnectionsConverter], add_default=True
            ),
        )

        # Up until here we have connection objects. Now we need
        # to resolve them to Nodes. The Nodes, as in 'connection.instance'
        #  are already loaded by the ZnDecoder.
        return handler.UpdateConnectors()(value)

    def get_stage_add_argument(self, instance) -> t.List[tuple]:
        """Get the dvc command for this field."""
        return [
            (f"--{self.dvc_option}", pathlib.Path(file).as_posix())
            for file in self.get_files(instance)
        ]
