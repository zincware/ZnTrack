import os
import pathlib
import shutil
import subprocess

import pytest

from zntrack.core.functions.decorator import NodeConfig, nodify


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


@nodify(outs="test.txt", params={"text": "Lorem"})
def example_func(cfg: NodeConfig):
    out_file = pathlib.Path(cfg.outs)
    out_file.write_text(cfg.params.text)


def test_example_func(proj_path):

    example_func()
    assert pathlib.Path("test.txt").read_text() == "Lorem"


@nodify(deps="test.txt", outs="test2.txt", params={"text": "Ipsum"})
def deps_func(cfg: NodeConfig):
    deps = pathlib.Path(cfg.deps)
    context = deps.read_text()
    outs = pathlib.Path(cfg.outs)
    outs.write_text(f"{context} {cfg.params.text}")


def test_deps_func(proj_path):
    example_func()
    deps_func()
    assert pathlib.Path("test.txt").read_text() == "Lorem"
    assert pathlib.Path("test2.txt").read_text() == "Lorem Ipsum"
