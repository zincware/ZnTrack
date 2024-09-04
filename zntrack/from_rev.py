import importlib
import pathlib
import sys

import dvc.repo


def from_rev(name: str, remote: str | None = None, rev: str | None = None):
    with dvc.repo.Repo(remote=remote, rev=rev) as repo:
        for stage in repo.index.stages:
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

    module = importlib.import_module(package_and_module)
    cls = getattr(module, cls_name)
    return cls.from_rev(name, remote=remote, rev=rev)
