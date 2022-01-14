import dataclasses
import logging

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Metadata:
    """Descriptor Metadata

    Attributes
    ----------
    dvc_option: str
        The command to be run by dvc, e.g. params
    zntrack_type: str
        Another identifier used by zntrack to distinguish e.g. zn from dvc descriptors
    """

    dvc_option: str
    zntrack_type: str

    @property
    def dvc_args(self):
        return self.dvc_option.replace("_", "-")


class Descriptor:
    """Python Descriptor with metadata

    This class allows to add metadata to arbitrary class arguments:

    >>> class HelloWorld
    >>>     value = Descriptor()
    >>>     def __init__(self):
    >>>         self.value = 25
    >>>
    >>> print(HelloWorld.value.metadata)
    >>> print(HelloWorld().value)

    References
    ----------
    https://docs.python.org/3/howto/descriptor.html
    """

    metadata: Metadata = None

    def __init__(self, default_value=None):
        """

        Parameters
        ----------
        default_value:
            Any default value to __get__ if the __set__ was never called.
        """
        self.default_value = default_value
        self.owner = None
        self.instance = None
        self.name = ""

    def __set_name__(self, owner, name):
        """Store name of the descriptor in the parent class"""
        self.owner = owner
        self.name = name

    def get(self, instance, owner):
        """Overwrite this method for custom get method"""
        raise NotImplementedError

    def set(self, instance, value):
        """Overwrite this method for custom set method"""
        raise NotImplementedError

    def __get__(self, instance, owner):
        """Get from instance.__dict__"""
        if instance is None:
            return self
        log.debug(f"Get {self} from {instance}")
        try:
            return self.get(instance, owner)
        except NotImplementedError:
            return instance.__dict__.get(self.name, self.default_value)

    def __set__(self, instance, value):
        """Save value to instance.__dict__"""
        log.debug(f"Set {self} from {instance}")
        try:
            self.set(instance, value)
        except NotImplementedError:
            instance.__dict__[self.name] = value
