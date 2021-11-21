"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Code for using subclasses / inheritance with ZnTrack
"""
import logging

from zntrack import dvc
from zntrack.utils.type_hints import TypeHintParent
import inspect
import abc

log = logging.getLogger(__name__)


class Child:
    # TODO this should probably consist of all dvc/zn types?
    deps: list = []
    outs: list = []
