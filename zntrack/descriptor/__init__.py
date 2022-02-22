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

    def __init__(self, default_value=None, **kwargs):
        """Define a Descriptor object

        Parameters
        ----------
        default_value:
            Any default value to __get__ if the __set__ was never called.
        """
        self._default_value = default_value
        self._owner = kwargs.get("owner")
        self._instance = kwargs.get("instance")
        self._name = kwargs.get("name", "")

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


def get_descriptors(cls, descriptor) -> list:
    """Get a list of all descriptors inheriting from "descriptor"

    Parameters
    ----------
    cls: any python class
    descriptor: any object inheriting from descriptor

    Returns
    -------
    list[Descriptor]
        a list of the found descriptor objects

    """
    lst = []
    for option in vars(type(cls)).values():
        if isinstance(option, descriptor):
            lst.append(option)
    return lst
