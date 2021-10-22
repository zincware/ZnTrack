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
class params(ZnTrackOption):
    option = "params"


class result(ZnTrackOption):
    option = "result"


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


# Deprecated method DVC, logging a DeprecationWarning:


class _log_DeprecationWarning:
    """Method to raise a DeprecationWarning."""

    def __set_name__(self, owner, name):
        """Descriptor default"""
        self.name = name

    def __get__(self, instance, owner):
        switcher = {
            "params": params,
            "result": result,
            "deps": deps,
            "outs": outs,
            "outs_no_cache": outs_no_cache,
            "outs_persistent": outs_persistent,
            "metrics": metrics,
            "metrics_no_cache": metrics_no_cache,
            "plots": plots,
            "plots_no_cache": plots_no_cache,
        }

        log.warning("DeprecationWarning: Please use zntrack.dvc instead of zntrack.DVC")

        return switcher[self.name]


class DVC:
    """Deprecated method DVC, logging a DeprecationWarning"""

    params = _log_DeprecationWarning()
    result = _log_DeprecationWarning()
    deps = _log_DeprecationWarning()

    outs = _log_DeprecationWarning()
    outs_no_cache = _log_DeprecationWarning()
    outs_persistent = _log_DeprecationWarning()

    metrics = _log_DeprecationWarning()
    metrics_no_cache = _log_DeprecationWarning()

    plots = _log_DeprecationWarning()
    plots_no_cache = _log_DeprecationWarning()
