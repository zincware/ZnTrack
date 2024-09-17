"""Module containing functions to finalize an experiment."""

import git


def make_commit(msg: str, path: str = ".") -> str:
    """Create a new GIT commit.

    Parameters
    ----------
    msg : str
        Commit message.
    path : str, optional
        Path to the GIT repository, by default "."

    Returns
    -------
    str
        The hash of the new commit.

    """
    if msg is None:
        msg = "zntrack: auto commit"
    repo = git.Repo(path)
    if repo.is_dirty():
        repo.git.add(".")
        repo.git.commit("-m", msg)
    return repo.head.commit.hexsha
