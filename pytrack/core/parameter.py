"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack parameter
"""


def parameter(obj=object):
    """Parameter for PyTrack

    Parameters
    ----------
    obj: any class object that the parameter will take on, so that type hinting does not raise issues

    Returns
    -------
    cls: Class that inherits from obj

    """

    class PyTrackParameter(obj):
        def __repr__(self):
            return "Empty PyTrack Parameter"

    return PyTrackParameter


def result(obj=object, outs=None):
    """Parameter for PyTrack

        Parameters
        ----------
        obj: any class object that the parameter will take on, so that type hinting does not raise issues
        outs: Future Version, allows for defining the type ot output

        Returns
        -------
        cls: Class that inherits from obj

        """

    class PyTrackResult(obj):
        def __init__(self):
            # TODO allow the definition of outs that are stored in GIT or DVC as an attribute
            self.outs = outs

        def __repr__(self):
            return "Empty PyTrack Result"

    return PyTrackResult
