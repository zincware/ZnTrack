import os
import pathlib
import shutil

from zntrack import Node, zn
from zntrack.project import ZnTrackProject


class SimpleNode(Node):
    inputs = zn.params()
    outputs = zn.outs()

    def __init__(self, inputs=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = inputs

    def run(self):
        self.outputs = self.inputs


def test_create_dvc_repo(tmp_path):
    os.chdir(tmp_path)
    ZnTrackProject().create_dvc_repository()
    assert pathlib.Path(".git").is_dir()
    assert pathlib.Path(".dvc").is_dir()


def test_destroy(tmp_path):
    os.chdir(tmp_path)
    ZnTrackProject().create_dvc_repository()
    ZnTrackProject()._destroy()
    assert not pathlib.Path(".dvc").is_dir()


def test_repro(tmp_path):
    os.chdir(tmp_path)
    shutil.copy(__file__, tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    SimpleNode(inputs=5).write_graph()

    project.repro()

    assert SimpleNode.load().outputs == 5


def test_run(tmp_path):
    os.chdir(tmp_path)
    shutil.copy(__file__, tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    SimpleNode(inputs=5).write_graph()

    project.run()

    assert SimpleNode.load().outputs == 5


def test_queue_and_run_all(tmp_path):
    os.chdir(tmp_path)
    shutil.copy(__file__, tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    SimpleNode(inputs=1).write_graph()
    project.queue(name="val1")
    SimpleNode(inputs=2).write_graph()
    project.queue(name="val2")

    project.run_all()

    project.load(name="val1")
    assert SimpleNode.load().outputs == 1
    project.load(name="val2")
    assert SimpleNode.load().outputs == 2
