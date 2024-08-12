import pathlib

import zntrack
from zntrack.utils import run_dvc_cmd


@zntrack.nodify(outs=pathlib.Path("test.txt"), params={"text": "Lorem Ipsum"})
def func_1(cfg: zntrack.NodeConfig):
    cfg.outs.write_text(cfg.params.text)


@zntrack.nodify(outs=pathlib.Path("test2.txt"), deps=pathlib.Path("test.txt"))
def func_2(cfg: zntrack.NodeConfig):
    cfg.outs.write_text(f"{cfg.deps.read_text()} 2")


@zntrack.nodify(outs=pathlib.Path("test3.txt"), deps=pathlib.Path("test.txt"))
def func_3(cfg: zntrack.NodeConfig):
    cfg.outs.write_text(f"{cfg.deps.read_text()} 3")


def test_example_func(proj_path):
    func_1_cfg = func_1()
    func_2_cfg = func_2()
    func_3_cfg = func_3()

    run_dvc_cmd(["repro"])

    assert func_1_cfg.outs.read_text() == "Lorem Ipsum"
    assert func_2_cfg.outs.read_text() == "Lorem Ipsum 2"
    assert func_3_cfg.outs.read_text() == "Lorem Ipsum 3"
