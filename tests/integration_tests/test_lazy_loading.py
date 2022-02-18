import os
import shutil
import subprocess

import pytest

from zntrack import zn
from zntrack.core.base import Node
from zntrack.utils import LazyOption


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class HelloWorld(Node):
    value = zn.params({"Lorem": "Ipsum"})

    def run(self):
        pass


def test_lazy_load(proj_path):
    hello_world = HelloWorld()
    hello_world.save()

    hello_world = HelloWorld.load(lazy=True)
    assert hello_world.__dict__["value"] is LazyOption
    assert hello_world.value == {"Lorem": "Ipsum"}


@pytest.mark.parametrize("lazy", (False, True))
def test_lazy_load_config(proj_path, lazy):
    """check that the config.lazy setting works"""
    from zntrack.utils import config

    config.lazy = lazy
    hello_world = HelloWorld()
    hello_world.save()

    hello_world = HelloWorld.load()
    if lazy:
        assert hello_world.__dict__["value"] is LazyOption
        assert hello_world.value == {"Lorem": "Ipsum"}
    else:
        assert hello_world.__dict__["value"] == {"Lorem": "Ipsum"}

    # always set it back to true after the tests, because it is global
    config.lazy = True


class StartValue(Node):
    params = zn.params("my param")
    outs = zn.outs()

    def run(self):
        self.outs = "start"


class MiddleValue(Node):
    start_value: StartValue = zn.deps(StartValue.load())
    params = zn.params("middle params")
    outs = zn.outs()

    def run(self):
        self.outs = "middle"


class StopValue(Node):
    middle_value: MiddleValue = zn.deps(MiddleValue.load())
    params = zn.params("stop value")
    outs = zn.outs()

    def run(self):
        self.outs = "stop"


def test_lazy_load_deps(proj_path):
    StartValue().write_graph(run=True)
    MiddleValue().write_graph(run=True)
    StopValue().write_graph(run=True)

    stop_val = StopValue.load(lazy=True)

    assert stop_val.__dict__["middle_value"] is LazyOption
    assert isinstance(stop_val.middle_value, MiddleValue)
    assert stop_val.middle_value.__dict__["outs"] is LazyOption
    assert stop_val.middle_value.outs == "middle"
    assert stop_val.middle_value.__dict__["outs"] == "middle"
    # one layer more
    assert stop_val.middle_value.__dict__["start_value"] is LazyOption
    assert isinstance(stop_val.middle_value.start_value, StartValue)


def test_not_lazy_load_deps(proj_path):
    StartValue().write_graph(run=True)
    MiddleValue().write_graph(run=True)
    StopValue().write_graph(run=True)

    stop_val = StopValue.load(lazy=False)

    # without lazy loading all values should be set in the __dict__
    assert isinstance(stop_val.__dict__["middle_value"], MiddleValue)
    assert isinstance(stop_val.middle_value.__dict__["start_value"], StartValue)
