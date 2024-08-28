import dataclasses
import json
import typing as t

import yaml
import znflow
import znjson

from zntrack.config import (
    PARAMS_FILE_PATH,
    ZNTRACK_FILE_PATH,
    ZNTRACK_LAZY_VALUE,
    ZNTRACK_OPTION,
    NodeStatusEnum,
    ZnTrackOptionEnum,
)
from zntrack.converter import ConnectionConverter, NodeConverter
from zntrack.plugins import ZnTrackPlugin
from zntrack.utils.misc import TempPathLoader
from zntrack.utils.node_wd import NWDReplaceHandler

if t.TYPE_CHECKING:
    from zntrack import Node


def _outs_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _metrics_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".json").write_text(znjson.dumps(getattr(self, name)))


def _plots_save_func(self: "Node", name: str):
    (self.nwd / name).with_suffix(".csv").write_text(getattr(self, name).to_csv())


def _deps_getter(self: "Node", name: str):
    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        return self.__dict__[name]

    with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        # TODO: Ensure deps are loaded from the correct revision
        content = znjson.loads(
            json.dumps(content),
            cls=znjson.ZnDecoder.from_converters(
                [NodeConverter, ConnectionConverter], add_default=True
            ),
        )

        # Resolve any connections in content
        if isinstance(content, list):
            content = [
                c.result if isinstance(c, znflow.Connection) else c for c in content
            ]
        elif isinstance(content, znflow.Connection):
            content = content.result

        self.__dict__[name] = content

    return getattr(self, name)


def _params_getter(self: "Node", name: str):
    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        return self.__dict__[name]

    with self.state.fs.open(PARAMS_FILE_PATH) as f:
        self.__dict__[name] = yaml.safe_load(f)[self.name][name]

    return getattr(self, name)


def _paths_getter(self: "Node", name: str):
    nwd_handler = NWDReplaceHandler()

    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        if self.state.state == NodeStatusEnum.RUNNING:
            return nwd_handler(self.__dict__[name], nwd=self.nwd)
        return self.__dict__[name]

    with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        content = znjson.loads(json.dumps(content))
        content = nwd_handler(content, nwd=self.nwd)

        if self.state.tmp_path is not None:
            loader = TempPathLoader()
            return loader(content, instance=self)

        return content


def _outs_getter(self: "Node", name: str):
    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        return self.__dict__[name]

    if self.state.state == NodeStatusEnum.RUNNING:
        return ZNTRACK_LAZY_VALUE

    with self.state.fs.open((self.nwd / name).with_suffix(".json")) as f:
        self.__dict__[name] = json.load(f)

    return getattr(self, name)


@dataclasses.dataclass
class DVCPlugin(ZnTrackPlugin):
    def getter(self, node: "Node", field: dataclasses.Field) -> t.Any:
        option = field.metadata.get(ZNTRACK_OPTION)

        if option == ZnTrackOptionEnum.DEPS:
            return _deps_getter(node, field.name)
        elif option == ZnTrackOptionEnum.PARAMS:
            return _params_getter(node, field.name)
        elif option in {
            ZnTrackOptionEnum.OUTS,
            ZnTrackOptionEnum.PLOTS,
            ZnTrackOptionEnum.METRICS,
        }:
            return _outs_getter(node, field.name)
        elif option in {
            ZnTrackOptionEnum.PARAMS_PATH,
            ZnTrackOptionEnum.DEPS_PATH,
            ZnTrackOptionEnum.OUTS_PATH,
            ZnTrackOptionEnum.PLOTS_PATH,
            ZnTrackOptionEnum.METRICS_PATH,
        }:
            return _paths_getter(node, field.name)

        raise ValueError(f"Unknown field metadata: {field.metadata}")

    def save(self, node: "Node", field: dataclasses.Field) -> None:
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.OUTS:
            _outs_save_func(node, field.name)
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS:
            _plots_save_func(node, field.name)
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
            _metrics_save_func(node, field.name)
