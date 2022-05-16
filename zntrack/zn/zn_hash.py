import datetime

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption


class Hash(ZnTrackOption):
    """Special ZnTrack outs

    This 'zn.Hash' can be useful if you are dealing with a Node that typically has no
    outputs but is used e.g. for storing parameters. Because other Nodes don't use the
    parameters of this Node but rather the outputs of this Node as a dependency,
    it is important that its value changes when ever parameters or dependencies change.

    TODO consider passing the parameters of such a Node to the dependent Node instead
     of using this trick.
    """

    zn_type = utils.ZnTypes.HASH
    dvc_option = utils.DVCOptions.OUTS_NO_CACHE.value
    allow_lazy: bool = False

    def __init__(self, *, use_time: bool = True, **kwargs):
        """

        Parameters
        ----------
        use_time: bool, default = True
            Add the hash of datetime.now() to provide extra salt for the hash value
            to change independently of the given parameters. This is the default,
            because rerunning the Node typically is associated with some changed
            dependencies which are not accounted for in the parameters.
        kwargs
        """
        super().__init__(filename="hash", **kwargs)
        self.use_time = use_time

    def __get__(self, instance, owner=None) -> int:
        """"""
        if instance is None:
            return self
        if self.use_time:
            return hash(instance) + hash(datetime.datetime.now())
        return hash(instance)

    def __set__(self, instance, value):
        """Don't allow to set the value"""
        raise ValueError("Can not set value of zn.Hash")
