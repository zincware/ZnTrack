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


@nodify(outs="test.txt", params={"text": "Lorem Ipsum"})
def example_func(cfg: NodeConfig) -> NodeConfig:
    out_file = pathlib.Path(cfg.outs)
    out_file.write_text(cfg.params.text)
    return cfg


def test_example_func(proj_path):
    example_func(run=True)
    assert pathlib.Path("test.txt").read_text() == "Lorem Ipsum"

    cfg = example_func(exec_func=True)
    assert cfg.outs == "test.txt"
    assert cfg.params == {"text": "Lorem Ipsum"}


def test_example_func_dry_run(proj_path):
    script = example_func(dry_run=True)
    assert " ".join(script) == " ".join(
        [
            "dvc",
            "run",
            "-n",
            "example_func",
            "--no-exec",
            "--force",
            "--params",
            "params.yaml:example_func",
            "--outs",
            "test.txt",
            'python -c "from test_single_function import '
            'example_func; example_func(exec_func=True)" ',
        ]
    )


@nodify(outs=[pathlib.Path("test.txt")], params={"text": "Lorem Ipsum"})
def example_func_lst_and_path(cfg: NodeConfig) -> NodeConfig:
    cfg.outs[0].write_text(cfg.params.text)
    return cfg


def test_example_func_lst_and_path(proj_path):
    example_func_lst_and_path(run=True)
    assert pathlib.Path("test.txt").read_text() == "Lorem Ipsum"

    cfg = example_func_lst_and_path(exec_func=True)
    assert cfg.outs == [pathlib.Path("test.txt")]
    assert cfg.params == {"text": "Lorem Ipsum"}


@nodify(outs=[pathlib.Path("test.txt")], params={})
def example_func_empty_params(cfg: NodeConfig) -> NodeConfig:
    cfg.outs[0].write_text("Lorem Ipsum")
    return cfg


def test_example_func_empty_params(proj_path):
    example_func_empty_params(run=True)
    assert pathlib.Path("test.txt").read_text() == "Lorem Ipsum"

    cfg = example_func_empty_params(exec_func=True)
    assert cfg.outs == [pathlib.Path("test.txt")]
    assert cfg.params == {}


def test_wrong_params():
    with pytest.raises(ValueError):

        @nodify(params="value")
        def node():
            pass


def test_wrong_outs():
    with pytest.raises(ValueError):

        @nodify(outs=25)
        def nodea():
            pass

    with pytest.raises(ValueError):

        @nodify(outs=[25, "str"])
        def nodeb():
            pass
