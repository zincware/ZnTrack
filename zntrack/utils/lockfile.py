import typing as t
from multiprocessing import Process, Queue

from dvc.api import DVCFileSystem
from dvc.stage.serialize import to_single_stage_lockfile


def get_stage_lock(name: str, queue: Queue) -> None:
    fs = DVCFileSystem()
    stage = next(iter(fs.repo.stage.collect(name)))
    stage.save_deps(allow_missing=False)
    result = to_single_stage_lockfile(stage)
    queue.put(result)  # Send the result back to the main process


def mp_start_stage_lock(name: str) -> t.Tuple[Queue, Process]:
    queue = Queue()
    p = Process(target=get_stage_lock, args=(name, queue))
    p.start()
    return queue, p


def mp_join_stage_lock(queue: Queue, p: Process) -> dict:
    p.join()
    stage_lock = queue.get()  # Receive the result
    return {k: v for k, v in stage_lock.items() if k in ["cmd", "deps", "params"]}
