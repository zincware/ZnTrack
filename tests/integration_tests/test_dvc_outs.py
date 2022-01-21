import os
import pathlib
import shutil
import subprocess

import pytest

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
    path1: pathlib.Path = dvc.outs()

    def __init__(self, path_x=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path1 = pathlib.Path(f"{path_x}.json")

    def run(self):
        self.path1.write_text("")


def test_load_dvc_outs(proj_path):
    SingleNode(path_x="test", name="1500").write_graph(no_exec=False)

    assert SingleNode.load(name="1500").path1 == pathlib.Path("test.json")
