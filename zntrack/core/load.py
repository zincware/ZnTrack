"""Load a node from a dvc stage."""

import contextlib
import importlib
import importlib.util
import json
import pathlib
import sys
import tempfile
import typing
import uuid

import dvc.api
import dvc.repo
import dvc.stage

from zntrack.core.node import Node
from zntrack.utils import config

T = typing.TypeVar("T", bound=Node)


def _get_stage(name, remote, rev) -> dvc.stage.PipelineStage:
    """Get a stage from a dvc.Repo."""
    with dvc.repo.Repo.open(url=remote, rev=rev) as repo:
        for stage in repo.index.stages:
            with contextlib.suppress(AttributeError):
                # non pipeline stage don't have name
                if stage.name == name:
                    return stage

        raise ValueError(
            f"Stage {name} not found in {remote}" + (f"/tree/{rev}" if rev else "")
        )


def _import_from_tempfile(package_and_module: str, remote, rev):
    """Create a temporary file to import from.

    Parameters
    ----------
    package_and_module : str
        The package and module to import, e.g. "zntrack.core.node.Node".
    remote : str
        The remote to load the module from.
    rev : str
        The revision to load the module from.

    Returns
    -------
    ModuleType
        The imported module.

    Raises
    ------
    ModuleNotFoundError
        If the module could not be found.
    FileNotFoundError
        If the file could not be found.
    """
    file = pathlib.Path(*package_and_module.split(".")).with_suffix(".py")
    fs = dvc.api.DVCFileSystem(url=remote, rev=rev)
    with tempfile.NamedTemporaryFile(suffix=".py") as temp_file, fs.open(file) as f:
        temp_file.write(f.read())
        temp_file.flush()

        # we use a random uuid to avoid name clashes
        ref_module = f"{uuid.uuid4()}.{package_and_module}"

        spec = importlib.util.spec_from_file_location(ref_module, temp_file.name)
        module = importlib.util.module_from_spec(spec)
        sys.modules[ref_module] = module
        spec.loader.exec_module(module)
        return module


def from_rev(name, remote=".", rev=None, **kwargs) -> T:
    """Load a ZnTrack Node by its name.

    Parameters
    ----------
    name : str|Node
        The name of the node.
    remote : str, optional
        The remote to load the node from. Defaults to workspace.
    rev : str, optional
        The revision to load the node from. Defaults to HEAD.
    **kwargs
        Additional keyword arguments to pass to the node's constructor.

    Returns
    -------
    Node
        The loaded node.
    """
    if isinstance(name, Node):
        name = name.name
    if "+" in name:
        fs = dvc.api.DVCFileSystem(url=remote, rev=rev)

        components = name.split("+")

        if len(components) == 3:
            parent, attribute, key = components
        else:
            parent, attribute = components
            key = None

        with fs.open(config.files.zntrack) as fs:
            zntrack_config = json.load(fs)
            data = zntrack_config[parent][attribute]
            if key is not None:
                try:
                    data = data[int(key)]
                except (ValueError, KeyError):
                    data = data[key]
            assert (
                data["_type"] == "zntrack.Node"
            ), f"Expected zntrack.Node, got {data['_type']}"
            package_and_module = data["value"]["module"]
            cls_name = data["value"]["cls"]
            module = None
    else:
        stage = _get_stage(name, remote, rev)

        cmd = stage.cmd
        run_str = cmd.split()[2]
        name = cmd.split()[4]

        package_and_module, cls_name = run_str.rsplit(".", 1)
        module = None
    try:
        module = importlib.import_module(package_and_module)
    except ModuleNotFoundError:
        with contextlib.suppress(FileNotFoundError, ModuleNotFoundError):
            module = _import_from_tempfile(package_and_module, remote, rev)

    if module is None:
        module_name = package_and_module.split(".")[0]
        raise ModuleNotFoundError(
            f"No module named '{module_name}'. The package might be available via 'pip"
            f" install {module_name}' or from the remote via 'pip install git+{remote}'."
        )

    cls = getattr(module, cls_name)

    return cls.from_rev(name, remote, rev, **kwargs)
