import pathlib

import pytest

from zntrack import Node, dvc, exceptions, utils, zn


class ListOfDataNode(Node):
    data: list = zn.outs()

    def run(self):
        with self.operating_directory() as new:
            if new:
                self.data = list(range(5))
                raise ValueError("Execution was interrupted")
            else:
                self.data += list(range(5, 10))


class RestartFromCheckpoint(Node):
    file: pathlib.Path = dvc.outs(utils.nwd / "out.txt")

    def run(self):
        with self.operating_directory() as new:
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


def test_remove_on_error(proj_path):
    node = RemoveOnError()
    node.write_graph()

    node = RemoveOnError.load()
    with pytest.raises(ValueError):
        node.run_and_save()

    nwd_new = node.nwd.with_name(f"ckpt_{node.nwd.name}")
    assert not nwd_new.exists()


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
