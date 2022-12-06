"""Description: zn.<option>.

The following can be used to store e.g. metrics directly without
defining and writing to a file explicitly. For more information on the individual methods
see https://dvc.org/doc/command-reference/run#options

"""

import contextlib
import logging

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption
from zntrack.zn.method import Method
from zntrack.zn.nodes import Nodes
from zntrack.zn.split_option import SplitZnTrackOption
from zntrack.zn.zn_hash import Hash

log = logging.getLogger(__name__)

__all__ = [Method.__name__, Hash.__name__, Nodes.__name__]

with contextlib.suppress(ImportError):
    from .plots import plots

    __all__ += [plots.__name__]


class outs(ZnTrackOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.RESULTS


class deps(ZnTrackOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DEPS
    file = utils.Files.zntrack

    def __get__(self, instance, owner=None, serialize=False):
        """Use load_node_dependency before returning the value."""
        if instance is None:
            return self
        value = super().__get__(instance, owner)
        value = utils.utils.load_node_dependency(value)  # use value = Cls.load()
        setattr(instance, self.name, value)
        return value


class metrics(ZnTrackOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = utils.DVCOptions.METRICS_NO_CACHE.value
    zn_type = utils.ZnTypes.RESULTS

    def __init__(self, *args, cache: bool = False, **kwargs):
        """Parse additional attributes for plots.

        Parameters
        ----------
        cache: bool, default = False
            Store the result of 'zn.metrics' inside the DVC cache.
            This can e.g. be useful it the metrics are large and should not be GIT tracked
        args:
            positional arguments passed super.__init__
        kwargs:
            keyword arguments passed super.__init__
        """
        if cache:
            self.dvc_option = utils.DVCOptions.METRICS.value
        super().__init__(*args, **kwargs)


class params(SplitZnTrackOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.PARAMS
    file = utils.Files.params


class metadata(ZnTrackOption):  # pylint: disable=invalid-name
    """Special ZnTrack option.

    This option defines a <metrics_no_cache> output that is used by ZnTracks metadata
    collectors.
    """

    dvc_option = utils.DVCOptions.METRICS_NO_CACHE.value
    zn_type = utils.ZnTypes.METADATA
