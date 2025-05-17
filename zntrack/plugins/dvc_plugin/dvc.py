import copy
import dataclasses
import json
import logging
import pathlib
import typing as t

import znflow
import znjson

from zntrack import config, converter
from zntrack.config import (
    FIELD_TYPE,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FIELD_SUFFIX,
    ZNTRACK_OPTION_PLOTS_CONFIG,
    FieldTypes,
)

# if t.TYPE_CHECKING:
from zntrack.node import Node
from zntrack.plugins import ZnTrackPlugin
from zntrack.plugins.dvc_plugin.params import deps_to_params
from zntrack.utils.misc import (
    RunDVCImportPathHandler,
    get_attr_always_list,
    sort_and_deduplicate,
)
from zntrack.utils.node_wd import NWDReplaceHandler, nwd
import typing as t

def params_path_to_dvc(self, field) -> list[dict[str, None]]:
    if getattr(self.node, field.name) is None:
        return []
    
    nwd_handler = NWDReplaceHandler()
    content = nwd_handler(
        get_attr_always_list(self.node, field.name), nwd=self.node.nwd
    )
    content = [
        {pathlib.Path(x).as_posix(): None} for x in content if x is not None
    ]
    return content

def outs_path_to_dvc(self, field) -> list[str]|list[dict]:
    if getattr(self.node, field.name) is None:
        return []
    if getattr(self.node, field.name) == nwd:
        raise ValueError(
            "Can not use 'zntrack.nwd' directly as an output path. "
            "Please use 'zntrack.nwd / <path/file>' instead."
        )
    nwd_handler = NWDReplaceHandler()
    content = nwd_handler(
        get_attr_always_list(self.node, field.name), nwd=self.node.nwd
    )
    content = [pathlib.Path(x).as_posix() for x in content if x is not None]
    if field.metadata.get(ZNTRACK_CACHE) is False:
        content = [{c: {"cache": False}} for c in content]
    return content


def plots_path_to_dvc(self, field) -> list[str]|list[dict]:
    if getattr(self.node, field.name) is None:
        return []
    nwd_handler = NWDReplaceHandler()
    content = nwd_handler(
        get_attr_always_list(self.node, field.name), nwd=self.node.nwd
    )
    content = [pathlib.Path(x).as_posix() for x in content if x is not None]
    if field.metadata.get(ZNTRACK_CACHE) is False:
        content = [{c: {"cache": False}} for c in content]
    return content
