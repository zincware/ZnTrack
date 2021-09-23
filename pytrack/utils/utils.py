"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""

import json


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


def raise_not_serializable(values: dict):
    """Raise an error with the non serializable objects selected

    If values is a dictionary, all entries will be checked, collected and then raised as ValueError
    This reduces the size of the ValueError message to only the important information.
    """

    if isinstance(values, dict):
        non_serializable = {}
        for key, val in values.items():
            if not is_jsonable(val):
                non_serializable.update({key: val})

        if len(non_serializable) > 0:
            raise ValueError(
                f"Passed values {non_serializable} are not JSON serializable."
            )

    if not is_jsonable(values):
        raise ValueError(f"{values} is not JSON serializable.")
