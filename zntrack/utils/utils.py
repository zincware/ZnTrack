"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""

import json
import os
import shutil
import tempfile
from zntrack.utils.config import config


# https://stackoverflow.com/questions/42033142/is-there-an-easy-way-to-check-if-an-object-is-json-serializable-in-python
def is_jsonable(x: dict) -> bool:
    """

    Parameters
    ----------
    x: dict
        Dictionary to check, if it is json serializable.

    Returns
    -------
    bool: Whether the dict was serializable or not.

    """
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


def cwd_temp_dir(required_files=None) -> tempfile.TemporaryDirectory:
    """Change into a temporary directory

    Helper for e.g. the docs to quickly change into a temporary directory
    and copy all files, e.g. the Notebook into that directory.

    Parameters
    ----------
    required_files: list, optional
        A list of optional files to be copied

    Returns
    -------
    temp_dir:
        The temporary  directory file. Close with temp_dir.cleanup() at the end.

    """
    temp_dir = tempfile.TemporaryDirectory()

    if config.nb_name is not None:
        shutil.copy(config.nb_name, temp_dir.name)
    if required_files is not None:
        for file in required_files:
            shutil.copy(file, temp_dir.name)

    os.chdir(temp_dir.name)

    return temp_dir
