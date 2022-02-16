import logging
import pathlib

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
    zntrack_type = utils.ZnTypes.params

    def get_filename(self, instance) -> pathlib.Path:
        """Does not really have a single file but params.yaml and zntrack.json"""
        return utils.Files.params

    def __get__(self, instance, owner):
        """Add some custom attributes to the instance to identify it in znjson"""
        if instance is None:
            return self
        log.debug(f"Get {self} from {instance}")
        value = instance.__dict__.get(self.name, self.default_value)
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
