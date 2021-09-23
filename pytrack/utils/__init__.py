"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Standard python init file for the utils directory
"""

from .utils import is_jsonable, raise_not_serializable
from .serializer import serializer, deserializer

__all__ = ["serializer", "deserializer", "raise_not_serializable"]
