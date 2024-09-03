import dataclasses
import json
import typing as t

import pandas as pd
import yaml
import znflow
import znjson

from zntrack.config import (
    PARAMS_FILE_PATH,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_FILE_PATH,
    ZNTRACK_LAZY_VALUE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.converter import (
    CombinedConnectionsConverter,
    ConnectionConverter,
    NodeConverter,
)
from zntrack.exceptions import NodeNotAvailableError
from zntrack.plugins import ZnTrackPlugin, base_getter
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


def _paths_getter(self: "Node", name: str):
    nwd_handler = NWDReplaceHandler()

    if name in self.__dict__ and self.__dict__[name] is not ZNTRACK_LAZY_VALUE:
        return nwd_handler(self.__dict__[name], nwd=self.nwd)
    try:
        with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
            content = json.load(f)[self.name][name]
            content = znjson.loads(json.dumps(content))
            content = nwd_handler(content, nwd=self.nwd)

            if self.state.tmp_path is not None:
                loader = TempPathLoader()
                return loader(content, instance=self)

            return content
    except FileNotFoundError:
        raise NodeNotAvailableError(f"Node '{self.name}' is not available")


def _deps_getter(self: "Node", name: str):
    with self.state.fs.open(ZNTRACK_FILE_PATH) as f:
        content = json.load(f)[self.name][name]
        # TODO: Ensure deps are loaded from the correct revision
        content = znjson.loads(
            json.dumps(content),
            cls=znjson.ZnDecoder.from_converters(
                [NodeConverter, ConnectionConverter, CombinedConnectionsConverter],
                add_default=True,
            ),
        )

        # Resolve any connections in content
        if isinstance(content, list):
            content = [
                (
                    c.result
                    if isinstance(c, (znflow.Connection, znflow.CombinedConnections))
                    else c
                )
                for c in content
            ]
        elif isinstance(content, (znflow.Connection, znflow.CombinedConnections)):
            content = content.result

        self.__dict__[name] = content


def _params_getter(self: "Node", name: str):
    with self.state.fs.open(PARAMS_FILE_PATH) as f:
        self.__dict__[name] = yaml.safe_load(f)[self.name][name]


def _outs_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".json")) as f:
        self.__dict__[name] = json.load(f)


def _plots_getter(self: "Node", name: str):
    with self.state.fs.open((self.nwd / name).with_suffix(".csv")) as f:
        self.__dict__[name] = pd.read_csv(f)


@dataclasses.dataclass
class DVCPlugin(ZnTrackPlugin):
    def getter(self, field: dataclasses.Field) -> t.Any:
        option = field.metadata.get(ZNTRACK_OPTION)

        if option == ZnTrackOptionEnum.DEPS:
            return base_getter(self.node, field.name, _deps_getter)
        elif option == ZnTrackOptionEnum.PARAMS:
            return base_getter(self.node, field.name, _params_getter)
        elif option == ZnTrackOptionEnum.PLOTS:
            return base_getter(self.node, field.name, _plots_getter)
        elif option in {
            ZnTrackOptionEnum.OUTS,
            ZnTrackOptionEnum.METRICS,
        }:
            return base_getter(self.node, field.name, _outs_getter)
        elif option in {
            ZnTrackOptionEnum.PARAMS_PATH,
            ZnTrackOptionEnum.DEPS_PATH,
            ZnTrackOptionEnum.OUTS_PATH,
            ZnTrackOptionEnum.PLOTS_PATH,
            ZnTrackOptionEnum.METRICS_PATH,
        }:
            return _paths_getter(self.node, field.name)
        return PLUGIN_EMPTY_RETRUN_VALUE

    def save(self, field: dataclasses.Field) -> None:
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.OUTS:
            _outs_save_func(self.node, field.name)
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS:
            _plots_save_func(self.node, field.name)
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
            _metrics_save_func(self.node, field.name)
