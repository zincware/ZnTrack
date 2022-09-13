import pathlib

import pytest

from zntrack import utils
from zntrack.core.functions.decorator import NodeConfig, nodify


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
            f'{utils.get_python_interpreter()} -c "from test_single_function import '
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


@nodify(outs={"data": pathlib.Path("data.txt")})
def example_func_with_outs_dict(cfg: NodeConfig):
    cfg.outs.data.write_text("Hello World")


def test_example_func_with_outs_dict(proj_path):
    example_func_with_outs_dict(run=True)
    assert pathlib.Path("data.txt").read_text() == "Hello World"


@nodify()
def function_no_args(cfg: NodeConfig):
    # not sure why this would ever be used, but it is possible
    pass


def test_function_no_args(proj_path):
    function_no_args(run=True)
