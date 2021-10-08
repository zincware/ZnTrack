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


class PyTrackProperty:
    """Map the correct pytrack instance to the correct cls

    This is required, because we use setattr(TYPE(cls)) and not on the
    instance, so we need to distinguish between different instances,
    otherwise there is only a single cls.pytrack for all instances!

    We save the PyTrack instance in self.__dict__ to avoid this.
    """

    def __init__(self, py_track_parent):
        # Need to do this here, because of ciruclar imports
        #  with the serializer
        self.py_track_parent = py_track_parent

    def __get__(self, instance, owner):
        """

        Parameters
        ----------
        instance: TypeHintParent
            An instance of the decorated function
        owner

        Returns
        -------
        PyTrack:
            the pytrack property to handle PyTrack
        """
        try:
            return instance.__dict__['pytrack']
        except KeyError:
            instance.__dict__['pytrack'] = self.py_track_parent(instance)
            return instance.__dict__['pytrack']

    def __set__(self, instance, value):
        raise NotImplementedError('Can not change pytrack property!')
