"""Load a node from a dvc stage."""

import contextlib
import importlib
import typing

import dvc.api
import dvc.repo
import dvc.stage

from zntrack.core.node import Node

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


def from_rev(name, remote=".", rev=None, **kwargs) -> T:
    """Load a Node."""
    stage = _get_stage(name, remote, rev)

    cmd = stage.cmd
    run_str = cmd.split()[2]
    name = cmd.split()[4]

    package_and_module, cls_name = run_str.rsplit(".", 1)
    try:
        module = importlib.import_module(package_and_module)
    except ModuleNotFoundError as err:
        module_name = package_and_module.split(".")[0]
        raise ModuleNotFoundError(
            f"No module named '{module_name}'. The package might be available via 'pip"
            f" install {module_name}' or from the remote via 'pip install git+{remote}'."
        ) from err

    cls = getattr(module, cls_name)

    return cls.from_rev(name, remote, rev, **kwargs)
