"""Description: zn.<option>

The following can be used to store e.g. metrics directly without
defining and writing to a file explicitly. For more information on the individual methods
see https://dvc.org/doc/command-reference/run#options

"""
import logging

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption
from zntrack.zn.method import Method
from zntrack.zn.split_option import SplitZnTrackOption

log = logging.getLogger(__name__)

__all__ = [Method.__name__]

try:
    from .plots import plots

    __all__ += [plots.__name__]
except ImportError:
    pass


# module class definitions to be used via zn.<option>
# detailed explanations on https://dvc.org/doc/command-reference/run#options
# with the exception that these will be loaded to memory when.
# for direct file references use dvc.<option> instead.


class outs(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.RESULTS


class deps(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DEPS
    file = utils.Files.zntrack

    def __get__(self, instance, owner):
        """Use load_node_dependency before returning the value"""
        if instance is None:
            return self
        value = super().__get__(instance, owner)
        value = utils.utils.load_node_dependency(value)  # use value = Cls.load()
        setattr(instance, self.name, value)
        return value


class metrics(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = utils.DVCOptions.METRICS_NO_CACHE.value
    zn_type = utils.ZnTypes.RESULTS


class params(SplitZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.PARAMS
    file = utils.Files.params


class iterable(ZnTrackOption):
    """Special ZnTrack option

    This option defines an iterable parameter for spawning nodes.
    """

    dvc_option = utils.DVCOptions.PARAMS.value
    zn_type = utils.ZnTypes.ITERABLE


class metadata(ZnTrackOption):
    """Special ZnTrack option

    This option defines a <metrics_no_cache> output that is used by ZnTracks metadata
    collectors.
    """

    dvc_option = utils.DVCOptions.METRICS_NO_CACHE.value
    zn_type = utils.ZnTypes.METADATA
