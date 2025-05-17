import copy
import dataclasses
import pathlib

import znflow

from zntrack import converter
from zntrack.config import (
    FIELD_TYPE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_SUFFIX,
    ZNTRACK_OPTION_PLOTS_CONFIG,
    FieldTypes,
)
from zntrack.node import Node
from zntrack.utils.misc import (
    RunDVCImportPathHandler,
    get_attr_always_list,
)
from zntrack.utils.node_wd import NWDReplaceHandler, nwd


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

def metrics_path_to_dvc(self, field) -> list[str]|list[dict]:
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

def outs_to_dvc(self, field) -> list[str]|list[dict]:
    suffix = field.metadata[ZNTRACK_FIELD_SUFFIX]
    content = [(self.node.nwd / field.name).with_suffix(suffix).as_posix()]
    if field.metadata.get(ZNTRACK_CACHE) is False:
        content = [{c: {"cache": False}} for c in content]
    return content

def metrics_to_dvc(self, field) -> list[str]|list[dict]:
    suffix = field.metadata[ZNTRACK_FIELD_SUFFIX]
    content = [(self.node.nwd / field.name).with_suffix(suffix).as_posix()]
    if field.metadata.get(ZNTRACK_CACHE) is False:
        content = [{c: {"cache": False}} for c in content]
    return content

def deps_path_to_dvc(self, field) -> list[str]:
    if getattr(self.node, field.name) is None:
        return []
    content = [
        pathlib.Path(c).as_posix()
        for c in get_attr_always_list(self.node, field.name)
        if c is not None
    ]
    RunDVCImportPathHandler()(self.node.__dict__.get(field.name))
    return content


def deps_to_dvc(self, field):
    deps_content = []
    params_content = []
    if getattr(self.node, field.name) is None:
        return deps_content, params_content
    nwd_handler = NWDReplaceHandler()
    content = get_attr_always_list(self.node, field.name)
    paths = []
    for con in content:
        if isinstance(con, (znflow.Connection)):
            if con.item is not None:
                raise NotImplementedError(
                    "znflow.Connection getitem is not supported yet."
                )
            paths.extend(
                converter.node_to_output_paths(con.instance, con.attribute)
            )
        elif isinstance(con, (znflow.CombinedConnections)):
            for _con in con.connections:
                if con.item is not None:
                    raise NotImplementedError(
                        "znflow.Connection getitem is not supported yet."
                    )
                paths.extend(
                    converter.node_to_output_paths(
                        _con.instance, _con.attribute
                    )
                )
        elif dataclasses.is_dataclass(con) and not isinstance(con, Node):
            for field in dataclasses.fields(con):
                if field.metadata.get(FIELD_TYPE) == FieldTypes.PARAMS_PATH:
                    # add the path to the params_path
                    content = nwd_handler(
                        get_attr_always_list(con, field.name),
                        nwd=self.node.nwd,
                    )
                    content = [
                        {pathlib.Path(x).as_posix(): None}
                        for x in content
                        if x is not None
                    ]
                    if len(content) > 0:
                        params_content.extend(content)
                        # stages.setdefault(FieldTypes.PARAMS.value, []).extend(
                        #     content
                        # )
                if field.metadata.get(FIELD_TYPE) == FieldTypes.DEPS_PATH:
                    content = [
                        pathlib.Path(c).as_posix()
                        for c in get_attr_always_list(con, field.name)
                        if c is not None
                    ]
                    if len(content) > 0:
                        deps_content.extend(content)
                        # stages.setdefault(FieldTypes.DEPS.value, []).extend(
                        #     content
                        # )

            # add node name to params.yaml
            # stages.setdefault(FieldTypes.PARAMS.value, []).append(
            #     self.node.name
            # )
            params_content.append(
                self.node.name
            )
        else:
            raise ValueError("unsupported type")
        
    return deps_content + paths, params_content


def plots_to_dvc(self, field):
    plots_content = []
    outs_content = []
    suffix = field.metadata[ZNTRACK_FIELD_SUFFIX]
    content = [(self.node.nwd / field.name).with_suffix(suffix).as_posix()]
    if field.metadata.get(ZNTRACK_CACHE) is False:
        content = [{c: {"cache": False}} for c in content]
    outs_content.extend(content)

    if ZNTRACK_OPTION_PLOTS_CONFIG in field.metadata:
        file_path = (
            (self.node.nwd / field.name).with_suffix(suffix).as_posix()
        )
        plots_config = field.metadata[ZNTRACK_OPTION_PLOTS_CONFIG].copy()
        if "x" not in plots_config or "y" not in plots_config:
            raise ValueError(
                "Both 'x' and 'y' must be specified in the plots_config."
            )
        if "x" in plots_config:
            plots_config["x"] = {file_path: plots_config["x"]}
        if isinstance(plots_config["y"], list):
            for idx, y in enumerate(plots_config["y"]):
                cfg = copy.deepcopy(plots_config)
                cfg["y"] = {file_path: y}
                plots_content.append({f"{self.node.name}_{field.name}_{idx}": cfg})
        else:
            if "y" in plots_config:
                plots_config["y"] = {file_path: plots_config["y"]}
            plots_content.append({f"{self.node.name}_{field.name}": plots_config})

    return outs_content, plots_content