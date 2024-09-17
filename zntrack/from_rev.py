import contextlib
import importlib
import importlib.util
import pathlib
import sys
import tempfile
import uuid

import dvc.api
import dvc.repo
import dvc.stage


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


def from_rev(name: str, remote: str | None = None, rev: str | None = None):
    fs = dvc.api.DVCFileSystem(url=remote, rev=rev)
    with fs.repo as repo:
        # with dvc.repo.Repo(remote=remote, rev=rev) as repo:
        for stage in repo.index.stages:
            with contextlib.suppress(AttributeError):
                # only PipelineStages have a name attribute
                if stage.name == name:
                    cmd = stage.cmd
                    break
        else:
            raise ValueError(f"Stage {name} not found in {repo}")

    # cmd will be "zntrack run module.name --name ..." and we need the module.name and --name part
    run_str = cmd.split()[2]
    name = cmd.split()[4]

    package_and_module, cls_name = run_str.rsplit(".", 1)

    sys.path.append(pathlib.Path.cwd().as_posix())

    try:
        module = importlib.import_module(package_and_module)
    except ModuleNotFoundError:
        try:
            module = _import_from_tempfile(package_and_module, remote, rev)
        except (FileNotFoundError, ModuleNotFoundError):
            module_name = package_and_module.split(".")[0]
            raise ModuleNotFoundError(
                f"No module named '{module_name}'. The package might be available via 'pip"
                f" install {module_name}' or from the remote via 'pip install git+{remote}'."
            )

    cls = getattr(module, cls_name)
    return cls.from_rev(name, remote=remote, rev=rev)
