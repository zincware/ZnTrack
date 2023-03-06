import os
import pathlib

import pytest
from typer.testing import CliRunner

from zntrack import Node, zn  # NodeConfig, nodify,
from zntrack.cli import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_version(runner):
    result = runner.invoke(app, ["--version"])
    assert "ZnTrack " in result.stdout  # ZnTrack v.x.y


def test_init(tmp_path, runner):
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert "Creating new project" in result.stdout

    assert pathlib.Path("src").is_dir()
    assert (pathlib.Path("src") / "__init__.py").is_file()
    assert pathlib.Path(".git").is_dir()
    assert pathlib.Path(".dvc").is_dir()
    assert pathlib.Path("main.py").is_file()
    assert pathlib.Path("README.md").is_file()


def test_init_gitignore(tmp_path, runner):
    os.chdir(tmp_path)
    _ = runner.invoke(app, ["init", "--gitignore"])

    assert pathlib.Path("src").is_dir()
    assert (pathlib.Path("src") / "__init__.py").is_file()
    assert pathlib.Path(".git").is_dir()
    assert pathlib.Path(".dvc").is_dir()
    assert pathlib.Path(".gitignore").is_file()
    assert pathlib.Path("main.py").is_file()
    assert pathlib.Path("README.md").is_file()


@pytest.mark.parametrize("force", (True, False))
def test_init_force(tmp_path, runner, force):
    os.chdir(tmp_path)
    pathlib.Path("file.txt").touch()

    if force:
        _ = runner.invoke(app, ["init", "--force"])
        assert pathlib.Path("src").is_dir()
        assert (pathlib.Path("src") / "__init__.py").is_file()
        assert pathlib.Path(".git").is_dir()
        assert pathlib.Path(".dvc").is_dir()
        assert pathlib.Path("main.py").is_file()
        assert pathlib.Path("README.md").is_file()
    else:
        _ = runner.invoke(app, ["init"])
        assert not pathlib.Path("src").exists()
        assert not pathlib.Path(".git").exists()
        assert not pathlib.Path(".dvc").exists()
        assert not pathlib.Path("main.py").exists()
        assert not pathlib.Path("README.md").exists()


class InputsToOutputs(Node):
    inputs = zn.params()
    outputs = zn.outs()

    def run(self):
        self.outputs = self.inputs


# @nodify(outs="test.txt", params={"text": "Lorem Ipsum"})
# def example_func(cfg: NodeConfig) -> NodeConfig:
#     out_file = pathlib.Path(cfg.outs)
#     out_file.write_text(cfg.params.text)
#     return cfg


def test_run(proj_path, runner):
    node = InputsToOutputs(inputs=15)
    node.write_graph()
    result = runner.invoke(app, ["run", "test_cli.InputsToOutputs"])
    assert result.exit_code == 0

    node.load()
    assert node.outputs == 15


# def test_run_nodify(proj_path, runner):
#     example_func()
#     result = runner.invoke(app, ["run", "test_cli.example_func"])
#     assert result.exit_code == 0
#     assert pathlib.Path("test.txt").read_text() == "Lorem Ipsum"


def test_run_w_name(proj_path, runner):
    node = InputsToOutputs(inputs=15, name="TestNode")
    node.write_graph()
    result = runner.invoke(app, ["run", "test_cli.InputsToOutputs", "--name", "TestNode"])
    assert result.exit_code == 0

    node.load()
    assert node.outputs == 15
