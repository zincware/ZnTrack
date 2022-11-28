"""Define a ZnTrack Method (deprecated)."""
import logging

from zntrack import utils
from zntrack.zn.split_option import SplitZnTrackOption

log = logging.getLogger(__name__)


class Method(SplitZnTrackOption):
    """ZnTrack methods passing descriptor.

    This descriptor allows to pass a class instance that is not a ZnTrack Node as a
    method that can be used later. It requires that all passed class attributes have
    the same name in the __init__ and via getattr and that they are serializable.

    Example.
    -------
    >>> class HelloWorld:
    >>>     def __init__(self, name):
    >>>         self.name = name
    >>>
    >>> class MyNode(zntrack.Node)
    >>>     my_method = Method()
    >>> MyNode().my_method = HelloWorld(name="Max")

    """

    dvc_option = utils.DVCOptions.PARAMS.value
    zn_type = utils.ZnTypes.PARAMS

    @utils.deprecated(
        reason=(
            "'zn.Method' should be replaced by 'zn.Nodes'. Upcoming issues with"
            " 'zn.Method' will probably not be fixed and it will be removed in future"
            " versions. Please be aware that 'zn.Nodes' is NOT a drop-in replacement."
        ),
        version="v0.4.3",
    )
    def __init__(self, *args, **kwargs):
        """Wrap init with deprecated descriptor."""
        super().__init__(*args, **kwargs)

    def get_filename(self, instance):
        """Does not have a single file but params.yaml and zntrack.json."""
        return None

    def __set__(self, instance, value):
        """Include type check for better error reporting."""
        # TODO raise error on default values,
        #  make compatible types an attribute of descriptor
        if utils.helpers.isnode(value):
            raise ValueError(
                f"zn.Method() does not support type <Node> ({value})."
                " Consider using zn.deps() / zn.Nodes() instead"
            )
        super().__set__(instance, value)

    def __get__(self, instance, owner=None, serialize=False):
        """Add some custom attributes to the instance to identify it in znjson."""
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
