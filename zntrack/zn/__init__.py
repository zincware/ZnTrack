"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: zn.<option>

The following can be used to store e.g. metrics directly without
defining and writing to a file
"""
import logging

from zntrack.core.parameter import ZnTrackOption

log = logging.getLogger(__name__)


# module class definitions to be used via zn.<option>
# detailed explanations on https://dvc.org/doc/command-reference/run#options
# with the exception that these will be loaded to memory when.
# for direct file references use dvc.<option> instead.


class outs(ZnTrackOption):
    option = "outs"
    load = True


# class plots(ZnTrackOption):
#     option = "plots"
#     load = True


class metrics(ZnTrackOption):
    option = "metrics"
    load = True
