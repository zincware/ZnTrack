import os
import pathlib
import shutil
import subprocess
import typing

import pytest
import yaml

from zntrack import dvc
from zntrack.core.base import Node


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class SingleNode(Node):
    path1: pathlib.Path = dvc.checkpoints()

    def __init__(self, path_x=None, **kwargs):
        super().__init__(**kwargs)
        self.path1 = pathlib.Path(f"{path_x}.json")

    def run(self):
        self.path1.write_text("Lorem Ipsum")


class SingleNodeListOut(Node):
    paths: typing.List[pathlib.Path] = dvc.checkpoints()

    def __init__(self, paths=None, **kwargs):
        super().__init__(**kwargs)
        self.paths = paths

    def run(self):
        for path in self.paths:
            path.write_text("Lorem Ipsum")


def test_load_dvc_outs(proj_path):
    SingleNode(path_x="test", name="1500").write_graph()

    assert SingleNode.load(name="1500").path1 == pathlib.Path("test.json")
    dvc_yaml = yaml.safe_load(pathlib.Path("dvc.yaml").read_text())
    assert dvc_yaml["stages"]["1500"]["outs"][0]["test.json"]["checkpoint"]


def test_multiple_outs(proj_path):
    SingleNodeListOut(
        paths=[pathlib.Path("test_1.txt"), pathlib.Path("test_2.txt")]
    ).write_graph()

    assert SingleNodeListOut.load().paths == [
        pathlib.Path("test_1.txt"),
        pathlib.Path("test_2.txt"),
    ]

    dvc_yaml = yaml.safe_load(pathlib.Path("dvc.yaml").read_text())
    assert dvc_yaml["stages"]["SingleNodeListOut"]["outs"][0]["test_1.txt"]["checkpoint"]
    assert dvc_yaml["stages"]["SingleNodeListOut"]["outs"][1]["test_2.txt"]["checkpoint"]
