"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Node decorators
"""


class Node:
    """Decorator for converting a class into a Node stage"""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Please see <migration tutorial>")
