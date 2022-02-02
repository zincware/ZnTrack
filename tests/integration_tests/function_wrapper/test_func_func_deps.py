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


@nodify(outs=pathlib.Path("test.txt"), params={"text": "Lorem Ipsum"})
def func_1(cfg: NodeConfig):
    cfg.outs.write_text(cfg.params.text)


@nodify(outs=pathlib.Path("test2.txt"), deps=pathlib.Path("test.txt"))
def func_2(cfg: NodeConfig):
    cfg.outs.write_text(cfg.deps.read_text() + " 2")


@nodify(outs=pathlib.Path("test3.txt"), deps=pathlib.Path("test.txt"))
def func_3(cfg: NodeConfig):
    cfg.outs.write_text(cfg.deps.read_text() + " 3")


def test_example_func(proj_path):
    func_1_cfg = func_1()
    func_2_cfg = func_2()
    func_3_cfg = func_3()

    subprocess.check_call(["dvc", "repro"])

    assert func_1_cfg.outs.read_text() == "Lorem Ipsum"
    assert func_2_cfg.outs.read_text() == "Lorem Ipsum 2"
    assert func_3_cfg.outs.read_text() == "Lorem Ipsum 3"
