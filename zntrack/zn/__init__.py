"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: zn.<option>

The following can be used to store e.g. metrics directly without
defining and writing to a file explicitly. For more information on the individual methods
see https://dvc.org/doc/command-reference/run#options

"""
import logging

from zntrack import utils
from zntrack.core.parameter import ZnTrackOption
from zntrack.descriptor import Metadata
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

    metadata = Metadata(dvc_option="outs", zntrack_type=utils.ZnTypes.results)


class deps(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    metadata = Metadata(dvc_option="deps", zntrack_type=utils.ZnTypes.deps)
    file = utils.Files.zntrack


class metrics(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    metadata = Metadata(dvc_option="metrics_no_cache", zntrack_type=utils.ZnTypes.results)


class params(SplitZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    metadata = Metadata(dvc_option="params", zntrack_type=utils.ZnTypes.params)
    file = utils.Files.params


class iterable(ZnTrackOption):
    """Special ZnTrack option

    This option defines an iterable parameter for spawning nodes.
    """

    metadata = Metadata(dvc_option="params", zntrack_type=utils.ZnTypes.iterable)


class metadata(ZnTrackOption):
    """Special ZnTrack option

    This option defines a <metrics_no_cache> output that is used by ZnTracks metadata
    collectors.
    """

    metadata = Metadata(
        dvc_option="metrics_no_cache", zntrack_type=utils.ZnTypes.metadata
    )
