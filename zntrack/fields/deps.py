import dataclasses
import functools
import json

import znfields
import znflow
import znflow.handler
import znflow.utils
import znjson

from zntrack import converter
from zntrack.config import (
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FILE_PATH,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter

from zntrack.fields.base import field
import dataclasses

def _deps_getter(self: "Node", name: str):
    with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        # TODO: Ensure deps are loaded from the correct revision
        content = znjson.loads(
            json.dumps(content),
            cls=znjson.ZnDecoder.from_converters(
                [
                    converter.NodeConverter,
                    converter.ConnectionConverter,
                    converter.CombinedConnectionsConverter,
                    converter.DVCImportPathConverter,
                    converter.DataclassConverter,
                ],
                add_default=True,
            ),
        )
        if isinstance(content, converter.DataclassContainer):
            content = content.get_with_params(self.name, name)
        if isinstance(content, list):
            new_content = []
            idx = 0
            for val in content:
                if isinstance(val, converter.DataclassContainer):
                    new_content.append(val.get_with_params(self.name, name, idx))
                    idx += 1  # index only runs over dataclasses
                else:
                    new_content.append(val)
            content = new_content

        content = znflow.handler.UpdateConnectors()(content)

        return content


def deps(default=dataclasses.MISSING, **kwargs):
    return field(default=default, load_fn=_deps_getter, zntrack_option=ZnTrackOptionEnum.DEPS, **kwargs)
