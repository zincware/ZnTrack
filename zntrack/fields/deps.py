import dataclasses
import json

import znflow
import znflow.handler
import znflow.utils
import znjson

from zntrack import converter
from zntrack.config import ZNTRACK_FILE_PATH, FieldTypes
from zntrack.fields.base import field
from zntrack.node import Node


def _deps_getter(self: "Node", name: str):
    with self.state.fs.open(self.state.path / ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        # TODO: Ensure deps are loaded from the correct revision
        content = znjson.loads(
            json.dumps(content),
            cls=znjson.ZnDecoder.from_converters(
                [
                    converter.create_node_converter(
                        remote=self.state.remote, rev=self.state.rev, path=self.state.path
                    ),
                    converter.ConnectionConverter,
                    converter.CombinedConnectionsConverter,
                    converter.DVCImportPathConverter,
                    converter.DataclassConverter,
                ],
                add_default=True,
            ),
        )
        if isinstance(content, converter.DataclassContainer):
            content = content.get_with_params(
                self.name, name, index=None, fs=self.state.fs, path=self.state.path
            )
        if isinstance(content, list):
            new_content = []
            idx = 0
            for val in content:
                if isinstance(val, converter.DataclassContainer):
                    new_content.append(
                        val.get_with_params(
                            self.name, name, idx, fs=self.state.fs, path=self.state.path
                        )
                    )
                    idx += 1  # index only runs over dataclasses
                else:
                    new_content.append(val)
            content = new_content

        content = znflow.handler.UpdateConnectors()(content)

        return content


def deps(default=dataclasses.MISSING, **kwargs):
    """Define dependencies for a node.

    A Node dependency field can be used to pass data from one node to another.
    It can not be used to pass anything that is not a ``zntrack.Node`` or a ``dataclass``.

    Parameters
    ----------
    default : Any, optional
        Should not be set on the class level.

    Examples
    --------
    >>> import zntrack
    >>> class MyFirstNode(zntrack.Node):
    ...     outs: int = zntrack.outs()
    ...
    ...     def run(self) -> None:
    ...         self.outs = 42
    ...
    >>> class MySecondNode(zntrack.Node):
    ...     deps: int = zntrack.deps()
    ...
    ...     def run(self) -> None: ...
    ...
    >>> with zntrack.Project() as project:
    ...     node1 = MyFirstNode()
    ...     node2 = MySecondNode(deps=node1.outs)
    >>> project.build()
    """
    return field(
        default=default,
        load_fn=_deps_getter,
        field_type=FieldTypes.DEPS,
        **kwargs,
    )
