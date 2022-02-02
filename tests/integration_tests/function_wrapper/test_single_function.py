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
def example_func(cfg: NodeConfig) -> NodeConfig:
    out_file = pathlib.Path(cfg.outs)
    out_file.write_text(cfg.params.text)
    return cfg


def test_example_func(proj_path):

    example_func(run=True)
    assert pathlib.Path("test.txt").read_text() == "Lorem"

    cfg = example_func(exec_func=True)
    assert cfg.outs == "test.txt"
    assert cfg.params == {"text": "Lorem"}
    assert cfg.deps is None


@nodify(outs=[pathlib.Path("test.txt")], params={"text": "Lorem"})
def example_func_lst_and_path(cfg: NodeConfig) -> NodeConfig:
    cfg.outs[0].write_text(cfg.params.text)
    return cfg


def test_example_func_lst_and_path(proj_path):

    example_func_lst_and_path(run=True)
    assert pathlib.Path("test.txt").read_text() == "Lorem"

    cfg = example_func_lst_and_path(exec_func=True)
    assert cfg.outs == [pathlib.Path("test.txt")]
    assert cfg.params == {"text": "Lorem"}
    assert cfg.deps is None
