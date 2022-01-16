import dataclasses
import os
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


@dataclasses.dataclass
class ExampleMethod:
    param1: int
    param2: int


class SingleNode(Node):
    data_class: ExampleMethod = zn.Method()
    dummy_param = zn.params(1)  # required to have some dependency
    result = zn.outs()

    def __init__(self, data_class=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_class = data_class

    def run(self):
        self.result = self.data_class.param1 + self.data_class.param2


def test_run_twice_diff_params(proj_path):
    SingleNode(data_class=ExampleMethod(1, 1)).write_graph()
    subprocess.check_call(["dvc", "repro"])
    assert SingleNode.load().result == 2
    # second run
    SingleNode(data_class=ExampleMethod(2, 2)).write_graph()
    subprocess.check_call(["dvc", "repro"])
    assert SingleNode.load().result == 4
