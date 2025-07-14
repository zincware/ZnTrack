import dataclasses
import json
import typing as t

import znflow
import znflow.handler
import znjson

from zntrack import converter
from zntrack.config import ZNTRACK_FILE_PATH, FieldTypes
from zntrack.fields.base import field
from zntrack.node import Node
from zntrack.utils.filesystem import resolve_state_file_path


def _deps_getter(self: "Node", name: str):
    zntrack_path = resolve_state_file_path(
        self.state.fs, self.state.path, ZNTRACK_FILE_PATH
    )

    with self.state.fs.open(zntrack_path) as f:
        content = json.load(f)[self.name][name]
        # TODO: Ensure deps are loaded from the correct revision
        try:
            content = znjson.loads(
                json.dumps(content),
                cls=znjson.ZnDecoder.from_converters(
                    [
                        converter.create_node_converter(
                            remote=self.state.remote or "",
                            rev=self.state.rev or "",
                            path=self.state.path,
                        ),
                        converter.ConnectionConverter,
                        converter.CombinedConnectionsConverter,
                        converter.DVCImportPathConverter,
                        converter.DataclassConverter,
                    ],
                    add_default=True,
                ),
            )
        except ModuleNotFoundError:
            # If external dataclass module can't be imported, return NOT_AVAILABLE
            # The enhanced NOT_AVAILABLE object will provide helpful errors when accessed
            from zntrack.config import NOT_AVAILABLE

            return NOT_AVAILABLE
        except AttributeError as e:
            # Only catch AttributeErrors related to missing module attributes
            if "module" in str(e).lower() or "attribute" in str(e).lower():
                from zntrack.config import NOT_AVAILABLE

                return NOT_AVAILABLE
            # Re-raise other AttributeErrors as they might indicate different issues
            raise
        if isinstance(content, converter.DataclassContainer):
            content = content.get_with_params(
                self.name,
                name,
                index=None,
                fs=self.state.fs,
                path=self.state.path,  # type: ignore
            )
        if isinstance(content, list):
            new_content = []
            idx = 0
            for val in content:
                if isinstance(val, converter.DataclassContainer):
                    new_content.append(
                        val.get_with_params(
                            self.name,
                            name,
                            idx,
                            fs=self.state.fs,
                            path=self.state.path,  # type: ignore
                        )
                    )
                    idx += 1  # index only runs over dataclasses
                else:
                    new_content.append(val)
            content = new_content

        content = znflow.handler.UpdateConnectors()(content)

        return content


def deps(default=dataclasses.MISSING, **kwargs) -> t.Any:
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
