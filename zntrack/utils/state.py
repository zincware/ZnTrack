import json
from pathlib import Path

import dvc.api
import dvc.fs
from dvc.stage.serialize import to_single_stage_lockfile


def get_node_status(
    addressing: str,
    remote: str | None,
    rev: str | None,
    fs: dvc.api.DVCFileSystem | None = None,
) -> bool | None:
    """Check if a node has changed since the last DVC run.

    Returns:
        - True if the node has changed
        - False if the node has not changed
        - None if the node does not exist or is not a zntrack node
    """

    # TODO: this should check the node status of all dependencies, and if
    # any of them has changed, the value should be set to None / unknown.
    if fs is None:
        fs = dvc.fs.DVCFileSystem(
            repo=remote,
            rev=rev,
        )
    try:
        stage = next(iter(fs.repo.stage.collect(addressing)))
    except Exception:
        return None
    stage.save_deps(allow_missing=True)
    dvc_lock = to_single_stage_lockfile(stage)
    dvc_lock = {k: v for k, v in dvc_lock.items() if k in ["cmd", "deps", "params"]}

    try:
        zntrack_meta = json.loads(
            fs.read_text(Path(stage.path_in_repo).parent / "zntrack.json"),
        )
    except FileNotFoundError:
        return None

    try:
        nwd = Path(zntrack_meta[stage.name]["nwd"]["value"])
    except KeyError:
        return None

    nwd_in_repo = Path(stage.path_in_repo).parent / nwd
    try:
        node_meta = json.loads(fs.read_text(nwd_in_repo / "node-meta.json"))
    except FileNotFoundError:
        return True

    try:
        node_lock = node_meta["lockfile"]
    except KeyError:
        return None  # old zntrack version

    # Compare dvc_lock with node_lock
    if dvc_lock == node_lock:
        return False
    else:
        return True
