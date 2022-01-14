import dataclasses
import os
import shutil
import subprocess

import pytest

from zntrack import zn
from zntrack.core.base import Node


class ExampleNode01(Node):
    inputs = zn.params()
    outputs = zn.outs()

    def __init__(self, inputs=None):
        super().__init__()
        self.inputs = inputs

    def run(self):
        self.outputs = self.inputs


@dataclasses.dataclass
class ExampleDataClsMethod:
    param1: float
    param2: float


class ExampleNodeWithDataClsMethod(Node):
    my_datacls: ExampleDataClsMethod = zn.Method()
    result = zn.outs()

    def __init__(self, method=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.my_datacls = method

    def run(self):
        self.result = self.my_datacls.param1 + self.my_datacls.param2


class ComputeMethod:
    def __init__(self, param1):
        self.param1 = param1

    def compute(self):
        return self.param1 * 10


class ExampleNodeWithCompMethod(Node):
    my_method: ComputeMethod = zn.Method()
    result = zn.outs()

    def __init__(self, method=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.my_method = method

    def run(self):
        self.result = self.my_method.compute()


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


def test_run(proj_path):
    test_node_1 = ExampleNode01(inputs="Lorem Ipsum")
    test_node_1.write_graph()

    subprocess.check_call(["dvc", "repro"])

    load_test_node_1 = ExampleNode01.load()
    assert load_test_node_1.outputs == "Lorem Ipsum"


def test_datacls_method(proj_path):
    example = ExampleNodeWithDataClsMethod(method=ExampleDataClsMethod(10, 20))
    example.write_graph()

    assert ExampleNodeWithDataClsMethod.load().my_datacls.param1 == 10
    assert ExampleNodeWithDataClsMethod.load().my_datacls.param2 == 20
    assert isinstance(
        ExampleNodeWithDataClsMethod.load().my_datacls, ExampleDataClsMethod
    )

    subprocess.check_call(["dvc", "repro"])

    assert ExampleNodeWithDataClsMethod.load().result == 30


def test_compute_method(proj_path):
    example = ExampleNodeWithCompMethod(method=ComputeMethod(5))
    example.write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert ExampleNodeWithCompMethod.load().result == 50


def test_metrics(proj_path):
    # TODO write something to zn.metrics and assert it with the result from dvc metrics ..
    pass
