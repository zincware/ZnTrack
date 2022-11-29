"""Collection of DVC options.

Based on ZnTrackOption python descriptors this gives access to them being used
to define e.g. dependencies

Examples
--------
>>> from zntrack import Node, dvc
>>> class HelloWorld(Node)
>>>     vars = dvc.params()

"""
import logging
import pathlib

from zntrack import utils
from zntrack.dvc.custom_base import DVCOption, PlotsModifyOption

log = logging.getLogger(__name__)


# All available DVC cmd options + results
# detailed explanations on https://dvc.org/doc/command-reference/run#options


class params(DVCOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class deps(DVCOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DEPS
    file = utils.Files.zntrack

    def __set__(self, instance, value):
        """Add a type check."""

        def check_correct_type(x):
            """Check if correct type is passed."""
            # TODO make this check available for more DVCOptions.
            if not (isinstance(x, (str, pathlib.Path)) or (x is None)):
                if hasattr(x, "node_name"):
                    raise ValueError(
                        f"Found Node instance ({x}) in dvc.deps(), use zn.deps() instead."
                    )
                raise ValueError(
                    f"Found type '{type(x)}', but 'dvc.deps' only supports lists/tuples"
                    " of string or Path."
                )

        if isinstance(value, (list, tuple)):
            [check_correct_type(x) for x in value]
        else:
            check_correct_type(value)

        super().__set__(instance, value)


class outs(DVCOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class checkpoints(DVCOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class outs_no_cache(DVCOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class outs_persistent(DVCOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class metrics(DVCOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class metrics_no_cache(DVCOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class plots(PlotsModifyOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


class plots_no_cache(PlotsModifyOption):  # pylint: disable=invalid-name
    """Identify DVC option.

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    zn_type = utils.ZnTypes.DVC
    file = utils.Files.zntrack


options = [
    params,
    deps,
    outs,
    checkpoints,
    outs_no_cache,
    outs_persistent,
    metrics,
    metrics_no_cache,
    plots,
    plots_no_cache,
]
