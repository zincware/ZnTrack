import contextlib
import importlib
import importlib.util
import pathlib
import sys

import dvc.api
import dvc.repo
import dvc.stage


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
        raise ModuleNotFoundError(
            f"No module found for '{package_and_module}'. The package might be available "
            f"via 'pip install {package_and_module}' or from the remote"
            f"via 'pip install git+{remote}'."
        )

    cls = getattr(module, cls_name)
    return cls.from_rev(name, remote=remote, rev=rev)
