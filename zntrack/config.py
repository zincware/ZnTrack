import enum
import pathlib

DVC_FILE_PATH = pathlib.Path("dvc.yaml")
PARAMS_FILE_PATH = pathlib.Path("params.yaml")
ZNTRACK_FILE_PATH = pathlib.Path("zntrack.json")
ENV_FILE_PATH = pathlib.Path("env.yaml")

ZNTRACK_OPTION = "zntrack.option"
ZNTRACK_CACHE = "zntrack.cache"
ZNTRACK_SAVE_FUNC = "zntrack.save_func"

ZNTRACK_DEFAULT = object()
ZNTRACK_LAZY_VALUE = object()


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
