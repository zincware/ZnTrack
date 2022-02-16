import json
import os
import pathlib
import shutil
import subprocess

import pytest

from zntrack import zn
from zntrack.core.base import Node


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class FirstNode(Node):
    outs = zn.outs()

    def run(self):
        self.outs = 42


class LastNode(Node):
    first_node: FirstNode = zn.deps(FirstNode.load())
    outs = zn.outs()

    def run(self):
        self.outs = self.first_node.outs / 2


def test_base_run(proj_path):
    FirstNode().write_graph(run=True)
    LastNode().write_graph(run=True)

    assert LastNode.load().outs == 21


@pytest.fixture()
def zntrack_dict() -> dict:
    return {
        "LastNode": {
            "first_node": {
                "_type": "ZnTrackType",
                "value": {
                    "cls": "FirstNode",
                    "lazy": True,
                    "module": "test_zn_deps",
                    "name": "FirstNode",
                },
            }
        }
    }


def test_assert_write_file(proj_path, zntrack_dict):
    FirstNode().write_graph()
    LastNode().write_graph()

    zntrack_dict_loaded = json.loads(pathlib.Path("zntrack.json").read_text())

    assert zntrack_dict_loaded == zntrack_dict


def test_assert_read_file(proj_path, zntrack_dict):
    pathlib.Path("zntrack.json").write_text(json.dumps(zntrack_dict))

    assert isinstance(LastNode.load().first_node, FirstNode)
