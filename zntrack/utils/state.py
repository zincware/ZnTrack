import dvc.api
import dvc.fs
import json

from dvc.stage.serialize import to_single_stage_lockfile
from pathlib import Path
import znjson



def get_node_status(addressing: str, remote: str|None, rev:str|None, fs: dvc.api.DVCFileSystem|None = None) -> bool | None:
    print(f"Checking node status for {addressing} in remote {remote} at revision {rev}")
    if fs is None:
        fs = dvc.fs.DVCFileSystem(
            repo=remote,
            rev=rev,
        )
    stage = next(iter(fs.repo.stage.collect(addressing)))
    stage.save_deps(allow_missing=True)
    dvc_lock = to_single_stage_lockfile(stage)
    dvc_lock = {k: v for k, v in dvc_lock.items() if k in ["cmd", "deps", "params"]}

    try:
        zntrack_meta = json.loads(
            fs.read_text(Path(stage.path_in_repo).parent / "zntrack.json"),
        )
    except FileNotFoundError:
        print(f"zntrack.json not found for {stage.name} at {stage.path_in_repo}")
        return None
    
    try:
        nwd = Path(zntrack_meta[stage.name]["nwd"]["value"])
    except KeyError:
        print(f"Node {stage.name} does not have a 'nwd' entry in zntrack.json")
        return None
    
    nwd_in_repo = Path(stage.path_in_repo).parent / nwd
    try:
        node_meta = json.loads(
            fs.read_text(nwd_in_repo / "node-meta.json")
        )
    except FileNotFoundError:
        print(f"node-meta.json not found for {stage.name} at {nwd_in_repo}")
        return False
    
    try:
        node_lock = node_meta["lockfile"]
    except KeyError:
        print(f"Node {stage.name} does not have a 'lockfile' entry in node-meta.json")
        return None # old zntrack version

    # Compare dvc_lock with node_lock
    if dvc_lock == node_lock:
        print(f"Node {stage.name} is unchanged.")
        return False
    else:
        print(f"Node {stage.name} has changed.")
        return True


