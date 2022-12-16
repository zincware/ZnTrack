import pathlib
import subprocess
import time

import pytest

import zntrack.utils.exceptions
from zntrack import Node, dvc, exceptions, utils, zn
from zntrack.utils.utils import dvc_unlock


class ListOfDataNode(Node):
    data: list = zn.outs()

    def run(self):
        with self.operating_directory(move_on=None) as new:
            if new:
                self.data = list(range(5))
                raise ValueError("Execution was interrupted")
            else:
                self.data += list(range(5, 10))


class RestartFromCheckpoint(Node):
    file: pathlib.Path = dvc.outs(utils.nwd / "out.txt")

    def run(self):
        with self.operating_directory(move_on=None) as new:
            if new:
                self.file.write_text("Hello")
                raise ValueError("Execution was interrupted")
            else:
                text = self.file.read_text()
                self.file.write_text(f"{text} there")


class RemoveOnError(Node):
    data: list = zn.outs()

    def run(self):
        with self.operating_directory(remove_on=(TypeError, ValueError)):
            raise ValueError("Execution was interrupted")


class MoveOnError(Node):
    data: list = zn.outs()

    def run(self):
        with self.operating_directory(move_on=(TypeError, ValueError)):
            self.data = list(range(5))
            raise ValueError("Execution was interrupted")


def test_remove_on_error(proj_path):
    node = RemoveOnError()
    node.write_graph()

    node = RemoveOnError.load()
    with pytest.raises(ValueError):
        node.run_and_save()

    nwd_new = node.nwd.with_name(f"ckpt_{node.nwd.name}")
    assert not nwd_new.exists()

    node = node.load()
    with pytest.raises(zntrack.utils.exceptions.DataNotAvailableError):
        _ = node.data


def test_move_on_error(proj_path):
    node = MoveOnError()
    node.write_graph()

    node = MoveOnError.load()
    with pytest.raises(ValueError):
        node.run_and_save()

    nwd_new = node.nwd.with_name(f"ckpt_{node.nwd.name}")
    assert not nwd_new.exists()
    #  the file exists but even if 'run_and_save' fails so the output can be investigated.
    node = node.load()
    assert node.data == list(range(5))


def test_ListOfDataNode(proj_path):
    ListOfDataNode().write_graph()

    node = ListOfDataNode.load()

    with pytest.raises(exceptions.DVCProcessError):
        utils.run_dvc_cmd(["repro"])
    nwd_new = node.nwd.with_name(f"ckpt_{node.nwd.name}")
    assert nwd_new.exists()
    utils.run_dvc_cmd(["repro"])
    assert not nwd_new.exists()

    assert ListOfDataNode.load().data == list(range(10))


def test_ListOfDataNode2(proj_path):
    node = ListOfDataNode()
    node.write_graph()

    with pytest.raises(ValueError):
        node.run_and_save()
    node.run_and_save()

    assert node.load().data == list(range(10))


def test_RestartFromCheckpoint(proj_path):
    RestartFromCheckpoint().write_graph()

    with pytest.raises(exceptions.DVCProcessError):
        utils.run_dvc_cmd(["repro"])

    assert not RestartFromCheckpoint.load().file.exists()
    utils.run_dvc_cmd(["repro"])

    assert RestartFromCheckpoint.load().file.read_text() == "Hello there"


def test_RestartFromCheckpoint2(proj_path):
    node = RestartFromCheckpoint()
    node.write_graph()

    with pytest.raises(ValueError):
        node.run_and_save()
    node.run_and_save()

    assert node.load().file.read_text() == "Hello there"


class WriteNumbersSlow(Node):
    outs = zn.outs()

    maximum = zn.params(10)

    def run(self):
        with self.operating_directory(move_on=None) as new:
            if new:
                self.outs = []
                for i in range(self.maximum):
                    time.sleep(0.1)
                    self.outs.append(i)
            else:
                start = self.outs[-1]
                for i in range(start, self.maximum):
                    time.sleep(0.1)
                    self.outs.append(i)


def test_kill_process(proj_path):
    node = WriteNumbersSlow()
    node.write_graph()
    zntrack.utils.run_dvc_cmd(["repro"])
    nwd_new = node.nwd.with_name(f"ckpt_{node.nwd.name}")
    assert not nwd_new.exists()
    assert node.load().outs == list(range(10))

    # and now we kill the process
    node = WriteNumbersSlow(maximum=100)
    node.write_graph()

    # killing the DVC process will not kill the python process as it would on
    #  a cluster
    proc = subprocess.Popen(["zntrack run ..."])
    time.sleep(1.5)
    proc.kill()
    assert nwd_new.exists()

    zntrack.utils.run_dvc_cmd(["repro"])
    nwd_new = node.nwd.with_name(f"ckpt_{node.nwd.name}")
    assert not nwd_new.exists()
    assert node.load().outs == list(range(100))
