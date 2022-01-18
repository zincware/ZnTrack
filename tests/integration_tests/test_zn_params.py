import json
import os
import pathlib
import shutil
import subprocess

import numpy as np
import pytest
import yaml

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
    """Test serialized data as parameters"""
    SingleNode(param1=pathlib.Path("test_file.json")).save()

    assert (
        yaml.safe_load(pathlib.Path("params.yaml").read_text())["SingleNode"]["param1"]
        == "test_file.json"
    )

    assert json.loads(pathlib.Path("zntrack.json").read_text())["SingleNode"] == {
        "param1": {"_type": "pathlib.Path"}
    }

    assert SingleNode.load().param1 == pathlib.Path("test_file.json")


def test_small_numpy_param(proj_path):
    SingleNode(param1=np.arange(4)).save()

    assert yaml.safe_load(pathlib.Path("params.yaml").read_text())["SingleNode"][
        "param1"
    ] == [0, 1, 2, 3]

    assert json.loads(pathlib.Path("zntrack.json").read_text())["SingleNode"] == {
        "param1": {"_type": "np.ndarray_small"}
    }

    np.testing.assert_array_equal(SingleNode.load().param1, np.arange(4))
