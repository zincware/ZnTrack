"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Type hinting class for IDE autocompletion
"""
from abc import ABC, abstractmethod

from zntrack.core.zntrack import ZnTrackParent


class TypeHintParent(ABC):
    """Parent class for all ZnTrack Nodes"""

    zntrack: ZnTrackParent

    def __call__(self, *args, **kwargs):
        """Default call method to save e.g. parameters"""
        pass

    @abstractmethod
    def run(self):
        """Run method to be called by DVC"""
        pass

    @classmethod
    def load(cls, name=None):
        if name is None:
            return cls(load=True)
        return cls(load=True, name=name)
