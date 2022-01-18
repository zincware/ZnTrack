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


class SingleNode(Node):
    param1 = zn.params()

    def __init__(self, param1=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.param1 = param1


def test_pathlib_param(proj_path):
    SingleNode(param1=pathlib.Path("test_file.json")).save()
