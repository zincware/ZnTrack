import logging

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption
from zntrack.utils import helpers
from zntrack.zn.zn_hash import Hash as ZnHash

log = logging.getLogger(__name__)


class Nodes(ZnTrackOption):
    """ZnTrack methods passing descriptor

    This descriptor allows to pass a class instance that is not a ZnTrack Node as a
    method that can be used later. It requires that all passed class attributes have
    the same name in the __init__ and via getattr an that they are serializable.

    Example
    --------
    >>> class HelloWorld:
    >>>     def __init__(self, name):
    >>>         self.name = name
    >>>
    >>> class MyNode(zntrack.Node)
    >>>     my_method = Method()
    >>> MyNode().my_method = HelloWorld(name="Max")

    """

    dvc_option = utils.DVCOptions.DEPS
    zn_type = utils.ZnTypes.DEPS
    file = utils.Files.zntrack

    def __set__(self, instance, value):
        """Include type check for better error reporting"""
        if not helpers.isnode(value):
            raise ValueError(
                f"zn.Nodes() only supports type <Node>. Found {type(value)} instead."
            )
        if len(value.zntrack.collect(ZnHash)) < 1:
            raise ValueError(
                "To use zn.Nodes the passed Node must have a zn.Hash "
                "attribute. This is required for generating an output even "
                "though the run method is not in use."
            )
        super().__set__(instance, value)

    def __get__(self, instance, owner=None):
        """Use load_node_dependency before returning the value"""
        if instance is None:
            return self
        value = super().__get__(instance, owner)
        value = utils.utils.load_node_dependency(value)  # use value = Cls.load()
        setattr(instance, self.name, value)
        return value
