import os
import pathlib

import pytest
import yaml
from typer.testing import CliRunner

import zntrack.examples
from zntrack import Node, NodeConfig, get_nodes, nodify, utils, zn
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


@nodify(outs="test.txt", params={"text": "Lorem Ipsum"})
def example_func(cfg: NodeConfig) -> NodeConfig:
    out_file = pathlib.Path(cfg.outs)
    out_file.write_text(cfg.params.text)
    return cfg


def test_run(proj_path, runner):
    with zntrack.Project() as proj:
        node = zntrack.examples.ParamsToOuts(params=15)

    proj.build()
    result = runner.invoke(app, ["run", "zntrack.examples.ParamsToOuts"])
    assert result.exit_code == 0

    node.load()
    assert node.outs == 15


def test_run_nodify(proj_path, runner):
    example_func()
    result = runner.invoke(app, ["run", "test_cli.example_func"])
    assert result.exit_code == 0
    assert pathlib.Path("test.txt").read_text() == "Lorem Ipsum"


def test_run_w_name(proj_path, runner):
    with zntrack.Project() as proj:
        node = zntrack.examples.ParamsToOuts(params=15, name="TestNode")

    proj.build()

    result = runner.invoke(
        app, ["run", "zntrack.examples.ParamsToOuts", "--name", "TestNode"]
    )
    assert result.exit_code == 0

    node.load()
    assert node.outs == 15


def test_list_groups(proj_path, runner):
    with zntrack.Project(automatic_node_names=True) as proj:
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)

    with proj.group("example1"):
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)

    # TODO: This is not working yet
    # with proj.group("nested"):
    #     _ = zntrack.examples.ParamsToOuts(params=15)
    #     _ = zntrack.examples.ParamsToOuts(params=15)

    with proj.group("nested", "GRP1"):
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)
    with proj.group("nested", "GRP2"):
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)

    proj.build()

    true_groups = {
        "example1": [
            "ParamsToOuts -> example1_ParamsToOuts",
            "ParamsToOuts_1 -> example1_ParamsToOuts_1",
        ],
        "nodes": [
            "ParamsToOuts",
            "ParamsToOuts_1",
        ],
        "nested": [
            {
                "GRP1": [
                    "ParamsToOuts -> nested_GRP1_ParamsToOuts",
                    "ParamsToOuts_1 -> nested_GRP1_ParamsToOuts_1",
                ],
                "GRP2": [
                    "ParamsToOuts -> nested_GRP2_ParamsToOuts",
                    "ParamsToOuts_1 -> nested_GRP2_ParamsToOuts_1",
                ],
            }
        ],
    }

    groups, _ = utils.cli.get_groups(remote=proj_path, rev=None)
    assert groups == true_groups

    result = runner.invoke(app, ["list", proj_path.as_posix()])
    # test stdout == yaml.dump of true_groups
    groups = yaml.safe_load(result.stdout)
    assert groups == true_groups

    assert result.exit_code == 0
