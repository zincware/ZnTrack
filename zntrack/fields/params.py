import dataclasses
import functools

import yaml
import znfields

from zntrack.config import (
    PARAMS_FILE_PATH,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter
from zntrack.fields.base import field
import dataclasses


def _params_getter(self: "Node", name: str):
    with self.state.fs.open(PARAMS_FILE_PATH) as f:
        return yaml.safe_load(f)[self.name][name]


def params(default=dataclasses.MISSING, **kwargs):
    # TODO: check types, do not allow e.g. connections or anything that can not be serialized
    return field(
        default=default,
        zntrack_option=ZnTrackOptionEnum.PARAMS,
        load_fn=_params_getter,
        suffix=None,
        cache=None,
        independent=None,
        **kwargs,
    )
