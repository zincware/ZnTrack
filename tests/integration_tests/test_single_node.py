import dataclasses
import json
import os
import pathlib
import shutil
import subprocess

import pytest

from zntrack import zn
from zntrack.core.base import Node


class ExampleNode01(Node):
    inputs = zn.params()
    outputs = zn.outs()

    def __init__(self, inputs=None, **kwargs):
        super().__init__(**kwargs)
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

    def __init__(self, method=None, **kwargs):
        super().__init__(**kwargs)
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

    def __init__(self, method=None, **kwargs):
        super().__init__(**kwargs)
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


def test_is_loaded(proj_path):
    ExampleNode01(inputs="Lorem Ipsum").save()

    assert not ExampleNode01().is_loaded
    assert ExampleNode01.load().is_loaded


def test_compute_method(proj_path):
    example = ExampleNodeWithCompMethod(method=ComputeMethod(5))
    example.write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert ExampleNodeWithCompMethod.load().result == 50


def test_overwrite_outs(proj_path):
    test_node_1 = ExampleNode01(inputs="Lorem Ipsum")
    out_file = pathlib.Path("nodes", "ExampleNode01", "outs.json")
    test_node_1.write_graph()

    # Do not create the file itself
    assert not out_file.exists()
    # Create the parent directory for .gitignore
    assert out_file.parent.exists()

    subprocess.check_call(["dvc", "repro"])

    # Now the file should exist after the Node ran.
    assert out_file.exists()


def test_metrics(proj_path):
    # TODO write something to zn.metrics and assert it with the result from dvc metrics ..
    pass


class HelloWorld(Node):
    argument_1 = zn.params()

    def __init__(self, argument_1=None, **kwargs):
        super().__init__(**kwargs)
        self.argument_1 = argument_1

    def run(self):
        pass


# Copy some tests from < 0.3 and adapt them


class HelloWorldwDefault(Node):
    argument_1 = zn.params(314159)

    def __init__(self, argument_1=None, **kwargs):
        super().__init__(**kwargs)
        if argument_1 is not None:
            self.argument_1 = argument_1

    def run(self):
        pass


def test_load_works(proj_path):
    """Test that pre-initializing zn.params does result in changing values"""

    HelloWorldwDefault(argument_1=11235).save()

    assert HelloWorldwDefault().argument_1 == 314159
    assert HelloWorldwDefault.load().argument_1 == 11235


class BasicTest(Node):
    """BasicTest class"""

    deps = zn.deps(
        [pathlib.Path("deps1", "input.json"), pathlib.Path("deps2", "input.json")]
    )
    parameters = zn.params()
    results = zn.outs()

    def __init__(self, test_name=None, test_values=None, **kwargs):
        """Constructor of the Node test instance"""
        super().__init__(**kwargs)
        self.parameters = {"test_name": test_name, "test_values": test_values}

    def run(self):
        """Run method of the Node test instance"""
        self.results = {"name": self.parameters["test_name"]}


@pytest.fixture()
def basic_test_node_fixture(proj_path):
    base = BasicTest(test_name="PyTest", test_values=[2, 4, 8, 16])
    for idx, dep in enumerate(base.deps):
        pathlib.Path(dep).parent.mkdir(exist_ok=True, parents=True)
        with open(dep, "w") as f:
            json.dump({"id": idx}, f)
    base.write_graph(no_exec=False)


def test_parameters(basic_test_node_fixture):
    """Test that the parameters are read correctly"""
    base = BasicTest.load()
    assert base.parameters == dict(test_name="PyTest", test_values=[2, 4, 8, 16])


def test_results(basic_test_node_fixture):
    """Test that the results are read correctly"""
    base = BasicTest.load()
    assert base.results == {"name": "PyTest"}


def test_deps(basic_test_node_fixture):
    """Test that the dependencies are stored correctly"""
    base = BasicTest.load()
    assert base.deps == [
        pathlib.Path("deps1", "input.json"),
        pathlib.Path("deps2", "input.json"),
    ]
