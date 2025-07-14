import importlib
import pathlib
import sys

import dvc.api
import git
from dvc.scm import SCMError
from dvc.stage.exceptions import StageFileDoesNotExistError


def from_rev(
    name: str,
    remote: str | None = None,
    rev: str | None = None,
    path: str | None = None,
    fs: dvc.api.DVCFileSystem | None = None,
):
    """Load a ZnTrack Node.

    Load an instance of any ZnTrack Node, given its name.

    Arguments
    ---------
    name : str
        The name of the ZnTrack Node to load.
        If multiple ``dvc.yaml`` files are present, the name should be
        specified as `path/to/dvc.yaml:NodeName`.
    remote : str, optional
        The remote URL where the DVC repository is located.
        If not provided, the current working directory will be used.
        Can be a local path or a remote URL (e.g., git repository).
    rev : str, optional
        The revision (commit hash, branch name, or tag) to load the Node from.
        If not provided, the current WORKSPACE revision will be used.
    fs: dvc.api.DVCFileSystem, optional
        A DVCFileSystem instance to use for accessing the DVC repository.
        If not provided, a new DVCFileSystem will be created using the `remote` and `rev`.
    """
    if path is not None:
        raise NotImplementedError
    if fs is None:
        fs = dvc.api.DVCFileSystem(url=remote, rev=rev)
    else:
        if remote is not None:
            raise ValueError(
                "If 'fs' is provided, 'remote' should be None. "
                "The remote is already specified in the DVCFileSystem."
            )
        if rev is not None:
            raise ValueError(
                "If 'fs' is provided, 'rev' should be None. "
                "The revision is already specified in the DVCFileSystem."
            )
        # get remote and rev from the fs
        remote = fs.repo.url
        try:
            rev = fs.repo.get_rev()
            # check if rev is the same as HEAD, then set to None
            try:
                if rev == git.Repo(fs.repo.root_dir).head.commit.hexsha:
                    rev = None
            except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
                # If we can't access the local git repo, just use the rev as-is
                pass
        except SCMError:
            rev = None
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

    # If we have a filesystem with a local repo, add it to Python path
    if fs is not None and hasattr(fs, "repo") and fs.repo is not None:
        repo_root = pathlib.Path(fs.repo.root_dir)
        if repo_root.exists():
            repo_root_str = str(repo_root)
            if repo_root_str not in sys.path:
                sys.path.insert(0, repo_root_str)

    try:
        module = importlib.import_module(package_and_module)
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            f"The node depends on package '{package_and_module}' which is not installed "
            f"in the current environment. You can install it via:\n"
            f"  pip install {package_and_module}\n"
            f"Or if it's available from the remote repository:\n"
            f"  pip install git+{remote if remote else 'REMOTE_URL'}"
        )

    cls = getattr(module, cls_name)
    return cls.from_rev(name, remote=remote, rev=rev, path=path, fs=fs)
