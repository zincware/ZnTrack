import pathlib

import pytest

from zntrack import dvc, zn
from zntrack.core.dvcgraph import (
    GraphWriter,
    get_dvc_arguments,
    handle_deps,
    handle_dvc,
)


class ExampleDVCOutsNode(GraphWriter):
    outs = dvc.outs(pathlib.Path("example.dat"))


def test_node_name_get():
    example = ExampleDVCOutsNode()
    assert example.node_name == "ExampleDVCOutsNode"
    example._node_name = "NamedExample"
    assert example.node_name == "NamedExample"


def test_get_dvc_arguments():
    assert get_dvc_arguments(
        {"force": True, "always_changed": False, "no_exec": True}
    ) == ["--force", "--no-exec"]


def test_handle_deps():
    assert handle_deps(["a.dat", "b.dat"]) == ["--deps", "a.dat", "--deps", "b.dat"]


def test_handle_deps_posix():
    """Change the path to posix for e.g. Windows users"""
    # TODO this does not really test anything, but I don't know how to fix that,
    #  because converting windows path to posix under linux does not work natively
    assert handle_deps(r"src\file.txt") in [
        ["--deps", "src/file.txt"],
        ["--deps", r"src\file.txt"],
    ]


def test_handle_dvc():
    assert handle_dvc(r"src\file.txt", "outs") in [
        ["--outs", "src/file.txt"],
        ["--outs", r"src\file.txt"],
    ]
    assert handle_dvc(["src/file.txt", "outs.txt"], "outs") == [
        "--outs",
        "src/file.txt",
        "--outs",
        "outs.txt",
    ]
    assert handle_dvc(("src/file.txt", "outs.txt"), "outs") == [
        "--outs",
        "src/file.txt",
        "--outs",
        "outs.txt",
    ]


def test_handle_deps_unknown():
    with pytest.raises(ValueError):
        handle_deps(handle_deps)


def test_handle_deps_node():
    assert handle_deps(ExampleDVCOutsNode()) == ["--deps", "example.dat"]


class ExampleAffectedFiles(GraphWriter):
    param = zn.params()
    zn_outs = zn.outs()
    zn_metrics = zn.metrics()
    dvc_outs = dvc.outs(pathlib.Path("dvc_outs.dat"))
    dvc_metrics = dvc.outs(pathlib.Path("dvc_metrics.json"))
    dvc_empty = dvc.outs()
    dvc_outs_lst = dvc.outs(["a.dat", "b.dat"])


def test_affected_files():
    example = ExampleAffectedFiles()

    assert example.affected_files == {
        pathlib.Path("dvc_metrics.json"),
        pathlib.Path("dvc_outs.dat"),
        pathlib.Path("nodes/ExampleAffectedFiles/metrics_no_cache.json"),
        pathlib.Path("nodes/ExampleAffectedFiles/outs.json"),
        "a.dat",
        "b.dat",
    }


class ExampleClassWithParams(GraphWriter):
    param1 = zn.params(default_value=1)
    param2 = zn.params(default_value=2)


def test__descriptor_list():
    example = ExampleClassWithParams()

    assert len(example._descriptor_list.data) == 2


def test_descriptor_list_filter():
    example = ExampleClassWithParams()

    assert example._descriptor_list.filter(zntrack_type="params") == {
        "param1": 1,
        "param2": 2,
    }

    assert example._descriptor_list.filter(
        zntrack_type="params", return_with_type=True
    ) == {"params": {"param1": 1, "param2": 2}}
