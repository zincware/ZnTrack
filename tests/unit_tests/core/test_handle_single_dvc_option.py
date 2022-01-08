import pathlib

import pytest

from zntrack.core.base import Node, handle_single_dvc_option
from zntrack.core.parameter import ZnTrackOption


@pytest.fixture()
def example_node_deps():
    class MyDeps(Node):
        outs = ZnTrackOption(option="outs", load=True)

        def run(self):
            pass

    class Mock:
        data = ZnTrackOption(option="deps")

        def __init__(self):
            self.data = MyDeps.load()

    mock = Mock()

    option = vars(type(mock))["data"]
    value = getattr(mock, "data")

    return option, value


@pytest.fixture()
def example_node_outs():
    class MyDeps(Node):
        outs = ZnTrackOption(option="outs", load=True)

        def run(self):
            pass

    class Mock:
        data = ZnTrackOption(option="outs")

        def __init__(self):
            self.data = MyDeps.load()

    mock = Mock()

    option = vars(type(mock))["data"]
    value = getattr(mock, "data")

    return option, value


@pytest.fixture()
def example_str():
    class Mock:
        data = ZnTrackOption(option="outs")

        def __init__(self):
            self.data = "file.json"

    mock = Mock()

    option = vars(type(mock))["data"]
    value = getattr(mock, "data")

    return option, value


@pytest.fixture()
def example_path():
    class Mock:
        data = ZnTrackOption(option="outs")

        def __init__(self):
            self.data = pathlib.Path("file.json")

    mock = Mock()

    option = vars(type(mock))["data"]
    value = getattr(mock, "data")

    return option, value


def test_handle_option(example_node_deps):
    assert handle_single_dvc_option(*example_node_deps) == [
        "--deps",
        pathlib.Path("nodes", "MyDeps", "outs.json"),
    ]


def test_handle_option_error(example_node_outs):
    with pytest.raises(NotImplementedError):
        _ = handle_single_dvc_option(*example_node_outs)


def test_handle_str(example_str):
    assert handle_single_dvc_option(*example_str) == ["--outs", "file.json"]


def test_handle_pathlib(example_path):
    assert handle_single_dvc_option(*example_path) == ["--outs", "file.json"]
