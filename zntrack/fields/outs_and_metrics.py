import json

import znjson

from zntrack.config import NOT_AVAILABLE, ZnTrackOptionEnum
from zntrack.fields.base import field
from zntrack.node import Node


def _outs_getter(self: "Node", name: str, suffix: str):
    with self.state.fs.open((self.nwd / name).with_suffix(suffix)) as f:
        return json.load(f, cls=znjson.ZnDecoder)


def _outs_save_func(self: "Node", name: str, suffix: str):
    (self.nwd / name).with_suffix(suffix).write_text(znjson.dumps(getattr(self, name)))


def _metrics_save_func(self: "Node", name: str, suffix: str):
    (self.nwd / name).with_suffix(suffix).write_text(json.dumps(getattr(self, name)))


def outs(*, cache: bool = True, independent: bool = False, **kwargs):
    return field(
        default=NOT_AVAILABLE,
        cache=cache,
        independent=independent,
        zntrack_option=ZnTrackOptionEnum.OUTS,
        dump_fn=_outs_save_func,
        suffix=".json",
        load_fn=_outs_getter,
        repr=False,
        init=False,
        **kwargs,
    )


def metrics(*, cache: bool = False, independent: bool = False, **kwargs):
    return field(
        default=NOT_AVAILABLE,
        cache=cache,
        independent=independent,
        zntrack_option=ZnTrackOptionEnum.METRICS,
        dump_fn=_metrics_save_func,
        suffix=".json",
        load_fn=_outs_getter,
        repr=False,
        init=False,
        **kwargs,
    )
