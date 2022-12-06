"""The ZnTrack Node class."""
import logging

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption
from zntrack.utils import helpers
from zntrack.zn.zn_hash import Hash as ZnHash

log = logging.getLogger(__name__)


class Nodes(ZnTrackOption):
    """Have a ZnTrack Node as an attribute to another (main) Node.

    If you want to use a method of another ZnTrack Node you can pass it
    as a zn.Nodes()
    """

    dvc_option = utils.DVCOptions.DEPS
    zn_type = utils.ZnTypes.DEPS
    file = utils.Files.zntrack

    def __init__(self, default=None, **kwargs):
        """Add a check before calling super."""
        if default is not None:
            raise ValueError(
                "zn.Nodes does not support default values because they can be mutable."
                " Please set the default value in the __init__"
            )

        super().__init__(default=default, **kwargs)

    def __set__(self, instance, value):
        """Include type check for better error reporting."""
        if value is None:
            return

        if isinstance(value, (list, tuple)):
            raise ValueError(
                "zn.Nodes only supports single Node instances. Found"
                f" {type(value)} instead. Consider using a zn.Node Option for each"
                " instead."
            )

        if not helpers.isnode(value, subclass=False):
            # Only allow instances
            raise ValueError(
                "zn.Nodes() only supports instances of 'zntrack.Node'. Found"
                f" {type(value)} instead."
            )
        if len(value.zntrack.collect(ZnHash)) < 1:
            raise ValueError(
                "To use zn.Nodes the passed Node must have a 'zn.Hash' "
                "attribute. This is required for generating an output even "
                "though the run method is not in use."
            )
        super().__set__(instance, value)

    def __get__(self, instance, owner=None, serialize=False):
        """Use load_node_dependency before returning the value."""
        if instance is None:
            return self
        value = super().__get__(instance, owner)
        if value is not None:
            value._is_attribute = True
            value.node_name = f"{instance.node_name}_{self.name}"
        # value._is_attribute = True # value can be None
        value = utils.utils.load_node_dependency(value)  # use value = Cls.load()
        setattr(instance, self.name, value)
        return value
