"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""


class NoneType:
    """Class for checking set values

    This class is never used outside of PyTrack, so it can be used
    to identify if the value has been changed via
    >>> value = NoneType
    >>> if value == NoneType:
    >>>     print("value is unchanged")
    >>> value = None
    >>> if value != NoneType:
    >>>     print("value changed")

    which can not be done with any built in python type
    """

    pass


class PyTrackType:
    """Class to check against to see if it is part of PyTrack

    In comparison to PyTrackStage this is used to identify initiated stages
    """
    pass


class PyTrackStage:
    """Class to identify PyTrackStages

    This is used internally to mark a class definition as a PyTrackStage.
    In comparison to PyTrackType this is used to mark a class as a Stage that has not
    been called.

    >>> type(vars(Stage)['pytrack']) == 'PyTrackProperty'
    # can not use the following:
    >>> type(vars(Stage())['pytrack']) == 'PyTrackType'

    """
    def __init__(self, cls):
        self.cls = cls

    def get(self):
        """Load the PyTrackStage"""
        return self.cls(load=True)

