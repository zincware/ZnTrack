"""ZnTrack structs and LazyOption."""
import enum


class LazyOption:
    """A LazyOption for lazy loading."""

    def __init__(self):
        """Prohibit instantiation of LazyOption."""
        raise ValueError(
            "Can not initialize LazyOption. If you expected something else open an "
            "issue at https://github.com/zincware/ZnTrack and describe how you got here."
        )


class ZnTypes(enum.Enum):
    """Collection of ZnTrack Types to identify descriptors beyond their dvc option.

    Attributes
    ----------
    results: most zn.<options> like zn.outs() / zn.metrics() use this one
    HASH: special type which will always be saved even if _is_attribute = True
    """

    DEPS = enum.auto()
    DVC = enum.auto()
    METADATA = enum.auto()
    # method = enum.auto()
    PARAMS = enum.auto()
    ITERABLE = enum.auto()
    RESULTS = enum.auto()
    PLOTS = enum.auto()
    HASH = enum.auto()
    META = enum.auto()


FILE_DVC_TRACKED = [ZnTypes.DVC]
# if the getattr(instance, self.name) is an affected file,
# e.g. the dvc.<outs> is a file / list of files

VALUE_DVC_TRACKED = [
    ZnTypes.RESULTS,
    ZnTypes.METADATA,
    ZnTypes.PLOTS,
    ZnTypes.HASH,
]

# The data is not tracked / used via any DVC command
GIT_TRACKED = [ZnTypes.META]


# if the internal file,
# e.g. in the case of zn.outs() like nodes/<node_name>/outs.json is an affected file


class DVCOptions(enum.Enum):
    """Available DVCOptions."""

    # Use enum over dataclass because it is iterable
    PARAMS = "params"
    DEPS = "deps"
    OUTS = "outs"
    CHECKPOINTS = "checkpoints"
    OUTS_NO_CACHE = "outs_no_cache"
    OUTS_PERSISTENT = "outs_persistent"
    METRICS = "metrics"
    METRICS_NO_CACHE = "metrics_no_cache"
    PLOTS = "plots"
    PLOTS_NO_CACHE = "plots_no_cache"
