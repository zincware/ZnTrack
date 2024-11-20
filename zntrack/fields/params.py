import dataclasses

import yaml

from zntrack.config import PARAMS_FILE_PATH, ZnTrackOptionEnum
from zntrack.fields.base import field
from zntrack.node import Node


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
