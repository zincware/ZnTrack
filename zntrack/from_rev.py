import importlib
import importlib.util
import pathlib
import sys

import dvc.api
import dvc.repo
import dvc.stage
from dvc.stage.exceptions import StageFileDoesNotExistError


def from_rev(
    name: str, remote: str | None = None, rev: str | None = None, path: str | None = None
):
    if path is not None:
        raise NotImplementedError
    fs = dvc.api.DVCFileSystem(url=remote, rev=rev)
    try:
        stage = fs.repo.stage.collect(target=name)[0]
    except StageFileDoesNotExistError:
        raise ValueError(f"Stage {name} not found in {fs.repo}")

    try:
        cmd = stage.cmd
        name = stage.name
        path = pathlib.Path(stage.path).parent
    except AttributeError:
        raise ValueError("Stage is not a ZnTrack pipeline stage.")

    # cmd will be "zntrack run module.name --name ..."
    # and we need the module.name and --name part
    run_str = cmd.split()[2]
    name = cmd.split()[4]

    package_and_module, cls_name = run_str.rsplit(".", 1)

    sys.path.append(pathlib.Path.cwd().as_posix())
    if remote is not None:
        # check if remote is a path that exists
        if pathlib.Path(remote).exists():
            sys.path.append(remote)

    try:
        module = importlib.import_module(package_and_module)
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            f"No module found for '{package_and_module}'. The package might be available "
            f"via 'pip install {package_and_module}' or from the remote"
            f"via 'pip install git+{remote}'."
        )

    cls = getattr(module, cls_name)
    return cls.from_rev(name, remote=remote, rev=rev, path=path)
