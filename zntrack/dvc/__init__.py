"""Collection of DVC options

Based on ZnTrackOption python descriptors this gives access to them being used
to define e.g. dependencies

Examples
--------
>>> from zntrack import Node, dvc
>>> class HelloWorld(Node)
>>>     vars = dvc.params()
"""
import logging

from zntrack import utils
from zntrack.dvc.custom_base import DVCOption, PlotsModifyOption

log = logging.getLogger(__name__)


# All available DVC cmd options + results
# detailed explanations on https://dvc.org/doc/command-reference/run#options


class params(DVCOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class deps(DVCOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DEPS
    file = utils.Files.zntrack

    def __get__(self, instance, owner=None):
        """Use load_node_dependency before returning the value"""
        if instance is None:
            return self
        value = super().__get__(instance, owner)
        value = utils.utils.load_node_dependency(value, log_warning=True)
        setattr(instance, self.name, value)
        return value


class outs(DVCOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class checkpoints(DVCOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class outs_no_cache(DVCOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class outs_persistent(DVCOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class metrics(DVCOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class metrics_no_cache(DVCOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class plots(PlotsModifyOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class plots_no_cache(PlotsModifyOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


__all__ = [
    params,
    deps,
    outs,
    checkpoints,
    outs_no_cache,
    outs_persistent,
    metrics,
    metrics_no_cache,
    plots,
    plots_no_cache,
]
