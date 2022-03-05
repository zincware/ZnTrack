"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Collection of DVC options

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
from zntrack.core.zntrackoption import ZnTrackOption

log = logging.getLogger(__name__)


# All available DVC cmd options + results
# detailed explanations on https://dvc.org/doc/command-reference/run#options


class params(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "params"
    zntrack_type = utils.ZnTypes.PARAMS
    file = utils.Files.params

    @utils.deprecated(reason="This Option was moved to zntrack.zn.params", version="v0.3")
    def __init__(self, default_value=None):
        super().__init__(default_value)


class deps(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "deps"
    zntrack_type = utils.ZnTypes.DEPS
    file = utils.Files.zntrack

    def __get__(self, instance, owner):
        """Use load_node_dependency before returning the value"""
        value = super(deps, self).__get__(instance, owner)
        value = utils.utils.load_node_dependency(value, log_warning=True)
        setattr(instance, self.name, value)
        return value


class outs(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "outs"
    zntrack_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class checkpoints(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "checkpoints"
    zntrack_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class outs_no_cache(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "outs_no_cache"
    zntrack_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class outs_persistent(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "outs_persistent"
    zntrack_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class metrics(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "metrics"
    zntrack_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class metrics_no_cache(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "metrics_no_cache"
    zntrack_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class plots(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "plots"
    zntrack_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class plots_no_cache(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    dvc_option = "plots_no_cache"
    zntrack_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack
