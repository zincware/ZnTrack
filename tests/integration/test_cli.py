import pytest
import yaml
from typer.testing import CliRunner

import zntrack
import zntrack.examples
from zntrack import utils
from zntrack.cli import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_version(runner):
    result = runner.invoke(app, ["--version"])
    assert "ZnTrack " in result.stdout  # ZnTrack v.x.y


def test_run(proj_path, runner):
    with zntrack.Project() as proj:
        node = zntrack.examples.ParamsToOuts(params=15)

    proj.build()
    result = runner.invoke(app, ["run", "zntrack.examples.ParamsToOuts"])
    assert result.exit_code == 0

    assert node.outs == 15


def test_run_w_name(proj_path, runner):
    with zntrack.Project() as proj:
        node = zntrack.examples.ParamsToOuts(params=15, name="TestNode")

    proj.build()

    result = runner.invoke(
        app, ["run", "zntrack.examples.ParamsToOuts", "--name", "TestNode"]
    )
    assert result.exit_code == 0

    assert node.outs == 15


def test_list_groups(proj_path, runner):
    with zntrack.Project() as proj:
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)

    with proj.group("example1"):
        _ = zntrack.examples.ParamsToOuts(params=15)
        _ = zntrack.examples.ParamsToOuts(params=15)

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


def test_list_multi_nested_groups(proj_path, runner):
    proj = zntrack.Project()

    with proj:
        zntrack.examples.ParamsToOuts(params=15)
        zntrack.examples.ParamsToOuts(params=15)

    with proj.group("dynamics"):
        zntrack.examples.ParamsToOuts(params=15)
        zntrack.examples.ParamsToOuts(params=15)

    with proj.group("dynamics", "400K"):
        zntrack.examples.ParamsToOuts(params=15)
        zntrack.examples.ParamsToOuts(params=15)

    with proj.group("dynamics", "400K", "B"):
        zntrack.examples.ParamsToOuts(params=15)
        zntrack.examples.ParamsToOuts(params=15)

    proj.build()

    true_groups = {
        "dynamics": [
            {
                "400K": [
                    {
                        "B": [
                            "ParamsToOuts -> dynamics_400K_B_ParamsToOuts",
                            "ParamsToOuts_1 -> dynamics_400K_B_ParamsToOuts_1",
                        ]
                    },
                    "ParamsToOuts -> dynamics_400K_ParamsToOuts",
                    "ParamsToOuts_1 -> dynamics_400K_ParamsToOuts_1",
                ]
            },
            "ParamsToOuts -> dynamics_ParamsToOuts",
            "ParamsToOuts_1 -> dynamics_ParamsToOuts_1",
        ],
        "nodes": ["ParamsToOuts", "ParamsToOuts_1"],
    }

    groups, _ = utils.cli.get_groups(remote=proj_path, rev=None)
    assert groups == true_groups

    result = runner.invoke(app, ["list", proj_path.as_posix()])
    assert result.exit_code == 0
    groups = yaml.safe_load(result.stdout)
    assert groups == true_groups
    assert result.exit_code == 0
