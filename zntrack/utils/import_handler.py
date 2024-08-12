import logging
import pathlib
import sys


log = logging.getLogger(__name__)


def module_handler(obj) -> str:
    """Get the module for the Node.

    There are three cases that have to be handled here:
        1. Run from __main__ should not have __main__ as module but
            the actual filename.
        2. Run from a Jupyter Notebook should not return the launchers name
            but __main__ because that might be used in tests
        3. Return the plain module if the above are not fulfilled.

    Parameters
    ----------
    obj:
        Any object that implements __module__

    """
    # if config.nb_name:
    #     try:
    #         return f"{config.nb_class_path}.{obj.__name__}"
    #     except AttributeError:
    #         return f"{config.nb_class_path}.{obj.__class__.__name__}"
    if obj.__module__ != "__main__":
        if hasattr(obj, "_module_"):  # allow module override
            return obj._module_
        return obj.__module__
    if pathlib.Path(sys.argv[0]).stem == "ipykernel_launcher":
        # special case for e.g. testing
        return obj.__module__
    return pathlib.Path(sys.argv[0]).stem
