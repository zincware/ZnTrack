import pathlib

from zntrack import dvc
from zntrack.core.base import Node, get_dvc_arguments, handle_deps


class ExampleDVCOutsNode(Node):
    outs = dvc.outs("example.dat")


def test_get_dvc_arguments():
    assert get_dvc_arguments(
        {"force": True, "always_changed": False, "no_exec": True}
    ) == ["--force", "--no-exec"]


def test_handle_deps():
    assert handle_deps(["a.dat", "b.dat"]) == ["--deps", "a.dat", "--deps", "b.dat"]


def test_handle_deps_node():
    assert handle_deps(ExampleDVCOutsNode()) == ["--deps", pathlib.Path("example.dat")]


def test_node_module():
    example = ExampleDVCOutsNode()
    assert example.module == "test_core_base"

    example._module = "src.base"
    assert example.module == "src.base"


def test_python_interpreter():
    example = ExampleDVCOutsNode()
    assert example.python_interpreter in ["python", "python3"]
