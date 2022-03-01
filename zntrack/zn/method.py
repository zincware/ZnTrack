import logging

from zntrack import utils
from zntrack.zn.split_option import SplitZnTrackOption

log = logging.getLogger(__name__)


class Method(SplitZnTrackOption):
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

    dvc_option = "params"
    zntrack_type = utils.ZnTypes.PARAMS

    def get_filename(self, instance):
        """Does not have a single file but params.yaml and zntrack.json"""
        return utils.Files.params, utils.Files.zntrack

    def __get__(self, instance, owner):
        """Add some custom attributes to the instance to identify it in znjson"""
        if instance is None:
            # this must be here, even though it is in the super call, what follows
            #  after does not work otherwise
            return self
        value = super().__get__(instance, owner)
        if value is None:
            log.warning(
                "Found NoneType but expected some class instance. Please open an issue on"
                " github.com/zincware/ZnTrack if this causes unexpected behaviour."
            )
            return
        try:
            # Set some attribute for the serializer
            value.znjson_zn_method = True
            value.znjson_module = instance.module
        except AttributeError:
            # could be list / tuple
            for element in value:
                element.znjson_zn_method = True
                element.znjson_module = instance.module
        return value
