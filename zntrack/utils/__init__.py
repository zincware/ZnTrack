"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Standard python init file for the utils directory
"""

from zntrack.utils import exceptions, file_io
from zntrack.utils.config import Files, ZnTypes, config
from zntrack.utils.utils import (
    check_type,
    cwd_temp_dir,
    decode_dict,
    deprecated,
    encode_dict,
    get_auto_init,
    get_python_interpreter,
    module_handler,
    module_to_path,
    run_dvc_cmd,
    update_nb_name,
)

__all__ = [
    "config",
    "cwd_temp_dir",
    "decode_dict",
    "encode_dict",
    "module_handler",
    "update_nb_name",
    "module_to_path",
    "deprecated",
    ZnTypes.__name__,
    "file_io",
    "exceptions",
    Files.__name__,
    "check_type",
    "get_python_interpreter",
    "run_dvc_cmd",
    "get_auto_init",
]


class LazyOption:
    def __init__(self):
        raise ValueError(
            "Can not initialize LazyOption. If you expected something else open an "
            "issue at https://github.com/zincware/ZnTrack and describe how you got here."
        )
