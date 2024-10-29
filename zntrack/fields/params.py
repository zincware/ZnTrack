import dataclasses
import functools
import json

import yaml
import znfields
import znflow
import znflow.handler
import znflow.utils
import znjson

from zntrack import converter
from zntrack.config import (
    PARAMS_FILE_PATH,
    ZNTRACK_FIELD_GETTER,
    ZNTRACK_FILE_PATH,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.node import Node
from zntrack.plugins import base_getter, plugin_getter


def _params_getter(self: "Node", name: str):
    with self.state.fs.open(PARAMS_FILE_PATH) as f:
        self.__dict__[name] = yaml.safe_load(f)[self.name][name]


def params(default=dataclasses.MISSING, **kwargs) -> znfields.field:
    # TODO: check types, do not allow e.g. connections or anything that can not be serialized
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.PARAMS
    kwargs["metadata"][ZNTRACK_FIELD_GETTER] = functools.partial(
        base_getter, func=_params_getter
    )
    return znfields.field(
        default=default,
        getter=plugin_getter,
        **kwargs,
    )
