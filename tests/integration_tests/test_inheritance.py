import os
import shutil
import subprocess

import pytest

from zntrack import Node, zn


@pytest.fixture()
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class InOuts(Node):
    inputs = zn.params()
    outputs = zn.outs()


class WriteData(InOuts):
    def run(self):
        self.outputs = self.inputs


class WriteDataWithInit(InOuts):
    def __init__(self, inputs=None, **kwargs):
        super().__init__(**kwargs)
        self.inputs = inputs

    def run(self):
        self.outputs = self.inputs


class InOutsWInit(Node):
    inputs = zn.params()
    outputs = zn.outs()

    def __init__(self, inputs=None, **kwargs):
        super().__init__(**kwargs)
        self.inputs = inputs


class WriteDataParentInit(InOutsWInit):
    def run(self):
        self.outputs = self.inputs


class WriteDataParentInitWithInit(InOutsWInit):
    def __init__(self, inputs=None, **kwargs):
        super().__init__(**kwargs)
        self.inputs = inputs

    def run(self):
        self.outputs = self.inputs


@pytest.mark.parametrize(
    "MyNode",
    (WriteData, WriteDataWithInit, WriteDataParentInit, WriteDataParentInitWithInit),
)
def test_simple_inheritance(proj_path, MyNode):
    MyNode(inputs="HelloWorld").write_graph(run=True)
    assert MyNode.load().outputs == "HelloWorld"
