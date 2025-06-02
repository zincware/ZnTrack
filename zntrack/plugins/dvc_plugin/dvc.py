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


def _handle_nwd_list(self, field):
    """Helper function to process lists of paths with NWD replacement."""
    if getattr(self.node, field.name) is None:
        return []
    nwd_handler = NWDReplaceHandler()
    return nwd_handler(get_attr_always_list(self.node, field.name), nwd=self.node.nwd)


def _paths_to_dvc_list(
    paths: list[str], as_dict: bool = False, cache: bool = True
) -> list[str] | list[dict]:
    """Helper function to convert lists of paths to DVC format."""
    content = [pathlib.Path(x).as_posix() for x in paths if x is not None]
    if not cache:
        return [{c: {"cache": False}} for c in content]
    return content if not as_dict else [{c: None} for c in content]


def params_path_to_dvc(self, field) -> list[str] | list[dict]:
    """Convert params_path field to DVC params format."""
    paths = _handle_nwd_list(self, field)
    return _paths_to_dvc_list(paths, as_dict=True)


def outs_path_to_dvc(self, field) -> list[str] | list[dict]:
    """Convert outs_path field to DVC outs format."""
    if getattr(self.node, field.name) == nwd:
        raise ValueError(
            "Can not use 'zntrack.nwd' directly as an output path. "
            "Please use 'zntrack.nwd / <path/file>' instead."
        )
    paths = _handle_nwd_list(self, field)
    return _paths_to_dvc_list(paths, cache=field.metadata.get(ZNTRACK_CACHE, True))


def plots_path_to_dvc(self, field) -> list[str] | list[dict]:
    """Convert plots_path field to DVC outs format."""
    paths = _handle_nwd_list(self, field)
    return _paths_to_dvc_list(paths, cache=field.metadata.get(ZNTRACK_CACHE, True))


def metrics_path_to_dvc(self, field) -> list[str] | list[dict]:
    """Convert metrics_path field to DVC metrics format."""
    paths = _handle_nwd_list(self, field)
    return _paths_to_dvc_list(paths, cache=field.metadata.get(ZNTRACK_CACHE, True))


def outs_to_dvc(self, field) -> list[str] | list[dict]:
    """Convert outs field to DVC outs format."""
    suffix = field.metadata[ZNTRACK_FIELD_SUFFIX]
    content = [(self.node.nwd / field.name).with_suffix(suffix).as_posix()]
    if field.metadata.get(ZNTRACK_CACHE) is False:
        return [{c: {"cache": False}} for c in content]
    return content


def metrics_to_dvc(self, field) -> list[str] | list[dict]:
    """Convert metrics field to DVC metrics format."""
    suffix = field.metadata[ZNTRACK_FIELD_SUFFIX]
    content = [(self.node.nwd / field.name).with_suffix(suffix).as_posix()]
    if field.metadata.get(ZNTRACK_CACHE) is False:
        return [{c: {"cache": False}} for c in content]
    return content


def deps_path_to_dvc(self, field) -> list[str]:
    """Convert deps_path field to DVC deps format."""
    if getattr(self.node, field.name) is None:
        return []
    content = [
        pathlib.Path(c).as_posix()
        for c in get_attr_always_list(self.node, field.name)
        if c is not None
    ]
    RunDVCImportPathHandler()(self.node.__dict__.get(field.name))
    return content


def deps_to_dvc(self, field) -> tuple[list[str], list[str]]:
    """Convert deps field to DVC deps and params format."""
    deps_content = []
    params_content = []
    if getattr(self.node, field.name) is None:
        return deps_content, params_content

    nwd_handler = NWDReplaceHandler()
    content = get_attr_always_list(self.node, field.name)
    paths = []

    for con in content:
        if isinstance(con, znflow.Connection):
            if con.item is not None:
                raise NotImplementedError(
                    "znflow.Connection getitem is not supported yet."
                )
            paths.extend(converter.node_to_output_paths(con.instance, con.attribute))
        elif isinstance(con, znflow.CombinedConnections):
            for _con in con.connections:
                if _con.item is not None:
                    raise NotImplementedError(
                        "znflow.Connection getitem is not supported yet."
                    )
                paths.extend(
                    converter.node_to_output_paths(_con.instance, _con.attribute)
                )
        elif dataclasses.is_dataclass(con) and not isinstance(con, Node):
            for sub_field in dataclasses.fields(con):
                field_type = sub_field.metadata.get(FIELD_TYPE)
                if field_type == FieldTypes.PARAMS_PATH:
                    content = nwd_handler(
                        get_attr_always_list(con, sub_field.name),
                        nwd=self.node.nwd,
                    )
                    param_paths = _paths_to_dvc_list(content, as_dict=True)
                    if param_paths:
                        params_content.extend(param_paths)
                elif field_type == FieldTypes.DEPS_PATH:
                    dep_paths = [
                        pathlib.Path(c).as_posix()
                        for c in get_attr_always_list(con, sub_field.name)
                        if c is not None
                    ]
                    if dep_paths:
                        deps_content.extend(dep_paths)
            params_content.append(self.node.name)  # Add node name to params
        else:
            raise ValueError(f"Unsupported type: {type(con)}")

    return deps_content + paths, params_content


def plots_to_dvc(self, field) -> tuple[list, list[dict]]:
    """Convert plots field to DVC outs and plots format."""
    outs_content = []
    plots_content = []
    suffix = field.metadata[ZNTRACK_FIELD_SUFFIX]
    file_path = (self.node.nwd / field.name).with_suffix(suffix).as_posix()
    outs_content.append(file_path)
    if field.metadata.get(ZNTRACK_CACHE) is False:
        outs_content = [{c: {"cache": False}} for c in outs_content]

    plots_config = field.metadata.get(ZNTRACK_OPTION_PLOTS_CONFIG)
    if plots_config:
        plots_config = plots_config.copy()
        if "x" not in plots_config or "y" not in plots_config:
            raise ValueError("Both 'x' and 'y' must be specified in the plots_config.")
        if "x" in plots_config:
            plots_config["x"] = {file_path: plots_config["x"]}
        if isinstance(plots_config["y"], list):
            for idx, y in enumerate(plots_config["y"]):
                cfg = copy.deepcopy(plots_config)
                cfg["y"] = {file_path: y}
                plots_content.append({f"{self.node.name}_{field.name}_{idx}": cfg})
        elif "y" in plots_config:
            plots_config["y"] = {file_path: plots_config["y"]}
            plots_content.append({f"{self.node.name}_{field.name}": plots_config})

    return outs_content, plots_content
