import json
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import typing

import znjson

from zntrack.utils.config import config
from zntrack.utils.exceptions import DVCProcessError

log = logging.getLogger(__name__)


def cwd_temp_dir(required_files=None) -> tempfile.TemporaryDirectory:
    """Change into a temporary directory

    Helper for e.g. the docs to quickly change into a temporary directory
    and copy all files, e.g. the Notebook into that directory.

    Parameters
    ----------
    required_files: list, optional
        A list of optional files to be copied

    Returns
    -------
    temp_dir:
        The temporary  directory file. Close with temp_dir.cleanup() at the end.

    """
    temp_dir = tempfile.TemporaryDirectory()  # add ignore_cleanup_errors=True in Py3.10?

    if config.nb_name is not None:
        shutil.copy(config.nb_name, temp_dir.name)
    if required_files is not None:
        for file in required_files:
            shutil.copy(file, temp_dir.name)

    os.chdir(temp_dir.name)

    return temp_dir


def deprecated(reason, version="v0.0.0"):
    """Depreciation Warning"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            log.critical(
                f"DeprecationWarning for {func.__name__}: {reason} (Deprecated since"
                f" {version})"
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def decode_dict(value):
    """Decode dict that was loaded without znjson"""
    return json.loads(json.dumps(value), cls=znjson.ZnDecoder)


def encode_dict(value) -> dict:
    """Encode value into a dict serialized with ZnJson"""
    return json.loads(json.dumps(value, cls=znjson.ZnEncoder))


def get_auto_init(fields: typing.List[str], super_init: typing.Callable):
    """Automatically create an __init__ based on fields

    Parameters
    ----------
    fields: list[str]
        A list of strings that will be used in the __init__, e.g. for [foo, bar]
        it will create __init__(self, foo=None, bar=None) using **kwargs
    super_init: Callable
        typically this is Node.__init__
    """

    def auto_init(self, **kwargs):
        """Wrapper for the __init__"""
        for field in fields:
            try:
                setattr(self, field, kwargs.pop(field))
            except KeyError:
                pass
        super_init(self, **kwargs)  # call the super_init explicitly instead of super

    # we add this attribute to the __init__ to make it identifiable
    auto_init._uses_auto_init = True

    return auto_init


def module_handler(obj) -> str:
    """Get the module for the Node

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
    if obj.__module__ == "__main__":
        if pathlib.Path(sys.argv[0]).stem == "ipykernel_launcher":
            # special case for e.g. testing
            return obj.__module__
        return pathlib.Path(sys.argv[0]).stem
    else:
        return obj.__module__


def check_type(
    obj, types, allow_iterable=False, allow_none=False, allow_dict=False
) -> bool:
    """Check if the obj is of any of the given types

    This includes recursive search for nested lists / dicts and fails
    if any of the values is not in types

    Parameters
    ----------
    obj: object to check
    types: single class or tuple of classes to check against
    allow_iterable: check list entries if a list is provided
    allow_none: accept None even if not in types.
    allow_dict: allow for {key: types}
    """
    if isinstance(obj, (list, tuple, set)) and allow_iterable:
        for value in obj:
            if check_type(value, types, allow_iterable, allow_none, allow_dict):
                continue
            return False
    elif isinstance(obj, dict) and allow_dict:
        for value in obj.values():
            if check_type(value, types, allow_iterable, allow_none, allow_dict):
                continue
            return False
    else:
        if allow_none and obj is None:
            return True
        if not isinstance(obj, types):
            return False

    return True


def update_nb_name(nb_name: str) -> str:
    """Check the config file for a nb_name if None provided"""
    if nb_name is None:
        return config.nb_name
    return nb_name


def module_to_path(module: str, suffix=".py") -> pathlib.Path:
    """convert module a.b.c to path(a/b/c)"""
    return pathlib.Path(*module.split(".")).with_suffix(suffix)


def get_python_interpreter() -> str:
    """Find the most suitable python interpreter

    Try to run subprocess check calls to see, which python interpreter
    should be selected

    Returns
    -------
    interpreter: str
        Name of the python interpreter that works with subprocess calls

    """

    for interpreter in ["python3", "python"]:
        try:
            subprocess.check_call(
                [interpreter, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log.debug(f"Using command {interpreter} for dvc!")
            return interpreter

        except subprocess.CalledProcessError:
            log.debug(f"{interpreter} is not working!")
        except FileNotFoundError as err:
            log.debug(err)
    raise ValueError(
        "Could not find a working python interpreter to work with subprocesses!"
    )


def run_dvc_cmd(script):
    """Run the DVC script via subprocess calls

    Parameters
    ----------
    script: list[str]
        A list of strings to pass the subprocess command

    """
    dvc_short_string = " ".join(script[:4])
    if len(script) > 4:
        dvc_short_string += " ..."
    log.warning(f"Running DVC command: '{dvc_short_string}'")
    try:
        # do not display the output if log.log_level > logging.INFO
        subprocess.run(script, check=True, capture_output=config.log_level > logging.INFO)
    except subprocess.CalledProcessError as err:
        raise DVCProcessError(
            f"Subprocess call with cmd: \n \"{' '.join(script)}\" \n"
            f"# failed after stdout: \n{err.stdout.decode()}"
            f"# with stderr: \n{err.stderr.decode()}"
        ) from err


def load_node_dependency(value, log_warning=False):
    """Load a Node dependency if passed only a class

    Parameters
    ----------
    value: anything
        This function creates an instance of value if it is a class of node. Otherwise,
        it does nothing.
    log_warning: bool
        Log a DepreciationWarning when used from dvc.deps()

    Returns
    -------
    value:
        If value was subclass of Node, it returns an instance of value, otherwise
        it returns value

    """
    from zntrack.core.base import Node

    if isinstance(value, (list, tuple)):
        value = [load_node_dependency(x, log_warning) for x in value]
    try:
        if issubclass(value, Node):
            value = value.load()
    except TypeError:
        # value is not a class
        pass
    if isinstance(value, Node) and log_warning:
        log.warning(
            f"DeprecationWarning: Found Node instance ({value}) in dvc.deps(), please use"
            " zn.deps() instead."
        )
    return value
