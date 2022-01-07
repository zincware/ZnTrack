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

>>> @Node()
>>> class HelloWorld
>>>     vars = dvc.params()
"""
import logging

from zntrack.core.parameter import ZnTrackOption

log = logging.getLogger(__name__)


# All available DVC cmd options + results
# detailed explanations on https://dvc.org/doc/command-reference/run#options


class params(ZnTrackOption):
    option = "params"


class deps(ZnTrackOption):
    option = "deps"


class outs(ZnTrackOption):
    option = "outs"


class outs_no_cache(ZnTrackOption):
    option = "outs_no_cache"


class outs_persistent(ZnTrackOption):
    option = "outs_persistent"


class metrics(ZnTrackOption):
    option = "metrics"


class metrics_no_cache(ZnTrackOption):
    option = "metrics_no_cache"


class plots(ZnTrackOption):
    option = "plots"


class plots_no_cache(ZnTrackOption):
    option = "plots_no_cache"
