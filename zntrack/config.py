import enum
import pathlib

import typing_extensions as tyex

DVC_FILE_PATH = pathlib.Path("dvc.yaml")
PARAMS_FILE_PATH = pathlib.Path("params.yaml")
ZNTRACK_FILE_PATH = pathlib.Path("zntrack.json")
ENV_FILE_PATH = pathlib.Path("env.yaml")
NWD_PATH = pathlib.Path("nodes")
EXP_INFO_PATH = pathlib.Path(".exp_info.yaml")


# For "node-meta.json" and "dvc stage add ... --metrics-no-cache" the default is using
# git tracked files. Setting this to True will override the default behavior to always
# use the DVC cache. If you have a DVC cache setup, this might be desirable, to avoid
# a mixture between DVC cache and git tracked files.
ALWAYS_CACHE: bool = True


# Use sentinel object for zntrack specific configurations. Use
# a class to give it a better repr.
class _FIELD_TYPE_TYPE:
    pass


FIELD_TYPE = _FIELD_TYPE_TYPE()


class _ZNTRACK_CACHE_TYPE:
    pass


ZNTRACK_CACHE = _ZNTRACK_CACHE_TYPE()


class _ZNTRACK_SAVE_FUNC_TYPE:
    pass


ZNTRACK_SAVE_FUNC = _ZNTRACK_SAVE_FUNC_TYPE()


class _NOT_AVAILABLE_TYPE:
    def __repr__(self) -> str:
        return "NOT_AVAILABLE"

    def __getattr__(self, name):
        # When someone tries to access an attribute on NOT_AVAILABLE,
        # raise a helpful error about missing external dependencies
        raise ModuleNotFoundError(
            f"Cannot access attribute '{name}' because the external dependency "
            f"is not available. This typically means an external package is not "
            f"installed in the current environment. Please ensure all required "
            f"dependencies are installed or available in your Python path."
        )


NOT_AVAILABLE = _NOT_AVAILABLE_TYPE()


class _ZNTRACK_LAZY_VALUE_TYPE:
    pass


ZNTRACK_LAZY_VALUE = _ZNTRACK_LAZY_VALUE_TYPE()


class _ZNTRACK_EMPTY_RETRUN_VALUE_TYPE:
    pass


PLUGIN_EMPTY_RETRUN_VALUE = _ZNTRACK_EMPTY_RETRUN_VALUE_TYPE()


class _ZNTRACK_INDEPENDENT_OUTPUT_TYPE:
    pass


ZNTRACK_INDEPENDENT_OUTPUT_TYPE = _ZNTRACK_INDEPENDENT_OUTPUT_TYPE()


class _ZNTRACK_OPTION_PLOTS_CONFIG:
    pass


ZNTRACK_OPTION_PLOTS_CONFIG = _ZNTRACK_OPTION_PLOTS_CONFIG()


class _ZNTRACK_FIELD_LOAD_TYPE:
    pass


# TODO: rename getter to align with dump to load
ZNTRACK_FIELD_LOAD = _ZNTRACK_FIELD_LOAD_TYPE()


class _ZNTRACK_FIELD_DUMP_TYPE:
    pass


ZNTRACK_FIELD_DUMP = _ZNTRACK_FIELD_DUMP_TYPE()


class _ZNTRACK_FIELD_SUFFIX_TYPE:
    pass


ZNTRACK_FIELD_SUFFIX = _ZNTRACK_FIELD_SUFFIX_TYPE()


class NodeStatusEnum(enum.Enum):
    CREATED = 0
    RUNNING = 2
    FINISHED = 3


class FieldTypes(str, enum.Enum):
    DEPS = "deps"
    PARAMS = "params"
    OUTS = "outs"
    PLOTS = "plots"
    METRICS = "metrics"

    PARAMS_PATH = "params_path"
    DEPS_PATH = "deps_path"
    OUTS_PATH = "outs_path"
    PLOTS_PATH = "plots_path"
    METRICS_PATH = "metrics_path"


@tyex.deprecated("ZnTrackOptionEnum is deprecated. Use FieldTypes instead.")
class ZnTrackOptionEnum(str, enum.Enum):
    DEPS = "deps"
    PARAMS = "params"
    OUTS = "outs"
    PLOTS = "plots"
    METRICS = "metrics"

    PARAMS_PATH = "params_path"
    DEPS_PATH = "deps_path"
    OUTS_PATH = "outs_path"
    PLOTS_PATH = "plots_path"
    METRICS_PATH = "metrics_path"
