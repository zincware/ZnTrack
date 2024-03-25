import pathlib

import pytest

import zntrack
from zntrack.utils import run_dvc_cmd


@zntrack.nodify(outs="test.txt", params={"text": "Lorem Ipsum"})
def example_func(cfg: zntrack.NodeConfig) -> zntrack.NodeConfig:
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
            "stage",
            "add",
            "-n",
            "example_func",
            "--force",
            "--params",
            "params.yaml:example_func",
            "--outs",
            "test.txt",
            "zntrack run test_single_function.example_func",
        ]
    )


@zntrack.nodify(outs=[pathlib.Path("test.txt")], params={"text": "Lorem Ipsum"})
def example_func_lst_and_path(cfg: zntrack.NodeConfig) -> zntrack.NodeConfig:
    cfg.outs[0].write_text(cfg.params.text)
    return cfg


def test_example_func_lst_and_path(proj_path):
    example_func_lst_and_path(run=True)
    assert pathlib.Path("test.txt").read_text() == "Lorem Ipsum"

    cfg = example_func_lst_and_path(exec_func=True)
    assert cfg.outs == [pathlib.Path("test.txt")]
    assert cfg.params == {"text": "Lorem Ipsum"}


@zntrack.nodify(outs=[pathlib.Path("test.txt")], params={})
def example_func_empty_params(cfg: zntrack.NodeConfig) -> zntrack.NodeConfig:
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

        @zntrack.nodify(params="value")
        def node():
            pass


def test_wrong_outs():
    with pytest.raises(ValueError):

        @zntrack.nodify(outs=25)
        def nodea():
            pass

    with pytest.raises(ValueError):

        @zntrack.nodify(outs=[25, "str"])
        def nodeb():
            pass


@zntrack.nodify(outs={"data": pathlib.Path("data.txt")})
def example_func_with_outs_dict(cfg: zntrack.NodeConfig):
    cfg.outs.data.write_text("Hello World")


def test_example_func_with_outs_dict(proj_path):
    example_func_with_outs_dict(run=True)
    assert pathlib.Path("data.txt").read_text() == "Hello World"


@zntrack.nodify()
def function_no_args(cfg: zntrack.NodeConfig):
    # not sure why this would ever be used, but it is possible
    pass


def test_function_no_args(proj_path):
    function_no_args(run=True)
