import enum
import pathlib

DVC_FILE_PATH = pathlib.Path("dvc.yaml")
PARAMS_FILE_PATH = pathlib.Path("params.yaml")
ZNTRACK_FILE_PATH = pathlib.Path("zntrack.json")
ENV_FILE_PATH = pathlib.Path("env.yaml")
NWD_PATH = pathlib.Path("nodes")
EXP_INFO_PATH = pathlib.Path(".exp_info.yaml")


# Use sentinel object for zntrack specific configurations. Use
# a class to give it a better repr.
class _ZNTRACK_OPTION_TYPE:
    pass


ZNTRACK_OPTION = _ZNTRACK_OPTION_TYPE()


class _ZNTRACK_CACHE_TYPE:
    pass


ZNTRACK_CACHE = _ZNTRACK_CACHE_TYPE()


class _ZNTRACK_SAVE_FUNC_TYPE:
    pass


ZNTRACK_SAVE_FUNC = _ZNTRACK_SAVE_FUNC_TYPE()


class _NOT_AVAILABLE_TYPE:
    def __repr__(self) -> str:
        return "NOT_AVAILABLE"


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


class NodeStatusEnum(enum.Enum):
    CREATED = 0
    RUNNING = 2
    FINISHED = 3


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
