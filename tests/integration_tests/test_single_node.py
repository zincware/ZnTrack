import dataclasses
import json
import os
import pathlib
import shutil
import subprocess

import pytest

from zntrack import dvc, zn
from zntrack.core.base import Node
from zntrack.utils.exceptions import DVCProcessError


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


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


def test_run(proj_path):
    test_node_1 = ExampleNode01(inputs="Lorem Ipsum")
    assert test_node_1.inputs == "Lorem Ipsum"
    test_node_1.write_graph()

    obj = ExampleNode01.load()
    assert obj.inputs == "Lorem Ipsum"

    subprocess.check_call(["dvc", "repro"])

    load_test_node_1 = ExampleNode01.load()
    assert load_test_node_1.outputs == "Lorem Ipsum"


def test_run_no_exec(proj_path):
    test_node_1 = ExampleNode01(inputs="Lorem Ipsum")
    test_node_1.write_graph(no_exec=False)

    load_test_node_1 = ExampleNode01.load()
    assert load_test_node_1.outputs == "Lorem Ipsum"


def test_run_exec(proj_path):
    test_node_1 = ExampleNode01(inputs="Lorem Ipsum")
    test_node_1.write_graph(run=True)

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


class MethodExample:
    pass


class DVCDepsNode(Node):
    dependency_file = zn.deps()
    other_one = zn.deps(None)
    # test interaction with zn.Method here
    method = zn.Method()

    def __init__(self, deps=None, **kwargs):
        super().__init__(**kwargs)
        if not self.is_loaded:
            self.dependency_file = deps
            self.method = MethodExample()


def test_dvc_deps_node(proj_path):
    DVCDepsNode("test_traj.txt", name="simple_test").save()
    assert DVCDepsNode.load(name="simple_test").dependency_file == "test_traj.txt"

    DVCDepsNode(pathlib.Path("test_traj.txt"), name="simple_test").save()
    assert DVCDepsNode.load(name="simple_test").dependency_file == pathlib.Path(
        "test_traj.txt"
    )


class SingleNodeNoInit(Node):
    param1 = zn.params()
    param2 = zn.params()

    result = zn.outs()

    def run(self):
        self.result = self.param1 + self.param2


def test_auto_init(proj_path):
    SingleNodeNoInit(param1=25, param2=42).write_graph(no_exec=False)

    assert SingleNodeNoInit.load().param1 == 25
    assert SingleNodeNoInit.load().param2 == 42
    assert SingleNodeNoInit.load().result == 25 + 42


class OutsNotWritten(Node):
    """Define an outs file that is not being created"""

    outs = dvc.outs("does_not_exist.txt")

    def run(self):
        pass


def test_OutsNotWritten(proj_path):
    with pytest.raises(DVCProcessError):
        OutsNotWritten().write_graph(run=True)


class PathAsParams(Node):
    path = zn.params()

    def run(self):
        pass


def test_PathAsParams(proj_path):
    PathAsParams(path=pathlib.Path("file.txt").resolve()).save()

    assert PathAsParams.load().path == pathlib.Path("file.txt").resolve()


def test_load_named_nodes(proj_path):
    ExampleNode01(name="Node01", inputs=42).write_graph(run=True)
    ExampleNode01(name="Node02", inputs=3.1415).write_graph(run=True)

    assert ExampleNode01["Node01"].outputs == 42
    assert ExampleNode01["Node02"].outputs == 3.1415

    # this will run load with name=Node01, lazy=True/False
    assert ExampleNode01[{"name": "Node01", "lazy": True}].outputs == 42
    assert ExampleNode01[{"name": "Node01", "lazy": False}].outputs == 42


def test_remove_from_graph(proj_path):
    dvc_yaml = pathlib.Path("dvc.yaml")
    ExampleNode01().write_graph()
    assert dvc_yaml.exists()
    ExampleNode01().remove_from_graph()
    assert not dvc_yaml.exists()
