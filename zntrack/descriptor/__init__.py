class Descriptor:
    """Simple Python Descriptor that allows adding

    This class allows to add metadata to arbitrary class arguments:

    References
    ----------
    https://docs.python.org/3/howto/descriptor.html

    Examples
    --------

    >>> from zntrack.descriptor import Descriptor
    >>>
    >>> class MyDescriptor(Descriptor):
    >>>     metadata = "Custom Metadata"
    >>>
    >>> class SomeCls:
    >>>     value = MyDescriptor()
    >>>     def __init__(self, value):
    >>>         self.value = value
    >>>
    >>> print(SomeCls.value.metadata)
    >>> # "Custom Metadata"


    """

    def __init__(self, default_value=None, owner=None, instance=None, name=""):
        """Define a Descriptor object

        Parameters
        ----------
        default_value:
            Any default value to __get__ if the __set__ was never called.
        """
        self._default_value = default_value
        self._owner = owner
        self._instance = instance
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def owner(self):
        return self._owner

    @property
    def instance(self):
        return self._instance

    @property
    def default_value(self):
        return self._default_value

    def __set_name__(self, owner, name):
        """Store name of the descriptor in the parent class"""
        self._owner = owner
        self._name = name

    def __get__(self, instance, owner):
        """Get from instance.__dict__"""
        self._instance = instance
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default_value)

    def __set__(self, instance, value):
        """Save value to instance.__dict__"""
        self._instance = instance
        instance.__dict__[self.name] = value


def get_descriptors(descriptor=None, *, self=None, cls=None) -> list:
    """Get a list of all descriptors inheriting from "descriptor"

    Parameters
    ----------
    cls: any python class
    self: any python class instance
    descriptor: any object inheriting from descriptor

    Returns
    -------
    list
        a list of the found descriptor objects

    """
    if self is None and cls is None:
        raise ValueError("Either self or cls must not be None")
    if self is not None and cls is not None:
        raise ValueError("Either self or cls must be None")
    if self is not None:
        cls = type(self)
    lst = []
    for option in dir(cls):
        try:
            value = getattr(cls, option)
            if isinstance(value, descriptor):
                lst.append(value)
        except AttributeError as err:
            raise AttributeError(
                "Trying to call ZnTrackOption.__get__(instance=None) to retreive the"
                " <ZnTrackOption>. Make sure you implemented that case in the __get__"
                " method."
            ) from err
    return lst
