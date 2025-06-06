import json

import pytest
from typer.testing import CliRunner

import zntrack
import zntrack.examples
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

    true_groups = [
        {
            "changed": False,
            "full_name": "ParamsToOuts",
            "group": [
                "__NO_GROUP__",
            ],
            "name": "ParamsToOuts",
        },
        {
            "changed": False,
            "full_name": "ParamsToOuts_1",
            "group": [
                "__NO_GROUP__",
            ],
            "name": "ParamsToOuts_1",
        },
        {
            "changed": False,
            "full_name": "example1_ParamsToOuts",
            "group": [
                "example1",
            ],
            "name": "example1_ParamsToOuts",
        },
        {
            "changed": False,
            "full_name": "example1_ParamsToOuts_1",
            "group": [
                "example1",
            ],
            "name": "example1_ParamsToOuts_1",
        },
        {
            "changed": False,
            "full_name": "nested_GRP1_ParamsToOuts",
            "group": [
                "nested",
                "GRP1",
            ],
            "name": "nested_GRP1_ParamsToOuts",
        },
        {
            "changed": False,
            "full_name": "nested_GRP1_ParamsToOuts_1",
            "group": [
                "nested",
                "GRP1",
            ],
            "name": "nested_GRP1_ParamsToOuts_1",
        },
        {
            "changed": False,
            "full_name": "nested_GRP2_ParamsToOuts",
            "group": [
                "nested",
                "GRP2",
            ],
            "name": "nested_GRP2_ParamsToOuts",
        },
        {
            "changed": False,
            "full_name": "nested_GRP2_ParamsToOuts_1",
            "group": [
                "nested",
                "GRP2",
            ],
            "name": "nested_GRP2_ParamsToOuts_1",
        },
    ]

    result = runner.invoke(app, ["list", proj_path.as_posix(), "--json"])
    groups = json.loads(result.stdout)
    assert groups == true_groups

    assert result.exit_code == 0

    result = runner.invoke(app, ["list", proj_path.as_posix()])
    assert result.exit_code == 0

    outs = """
📁 No Group
├── ParamsToOuts ✅
└── ParamsToOuts_1 ✅
📁 example1
├── example1_ParamsToOuts ✅
└── example1_ParamsToOuts_1 ✅
📁 nested
├── 📁 GRP1
│   ├── nested_GRP1_ParamsToOuts ✅
│   └── nested_GRP1_ParamsToOuts_1 ✅
└── 📁 GRP2
    ├── nested_GRP2_ParamsToOuts ✅
    └── nested_GRP2_ParamsToOuts_1 ✅
"""
    assert result.stdout in outs


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

    true_groups = [
        {
            "changed": False,
            "full_name": "ParamsToOuts",
            "group": [
                "__NO_GROUP__",
            ],
            "name": "ParamsToOuts",
        },
        {
            "changed": False,
            "full_name": "ParamsToOuts_1",
            "group": [
                "__NO_GROUP__",
            ],
            "name": "ParamsToOuts_1",
        },
        {
            "changed": False,
            "full_name": "dynamics_400K_B_ParamsToOuts",
            "group": [
                "dynamics",
                "400K",
                "B",
            ],
            "name": "dynamics_400K_B_ParamsToOuts",
        },
        {
            "changed": False,
            "full_name": "dynamics_400K_B_ParamsToOuts_1",
            "group": [
                "dynamics",
                "400K",
                "B",
            ],
            "name": "dynamics_400K_B_ParamsToOuts_1",
        },
        {
            "changed": False,
            "full_name": "dynamics_400K_ParamsToOuts",
            "group": [
                "dynamics",
                "400K",
            ],
            "name": "dynamics_400K_ParamsToOuts",
        },
        {
            "changed": False,
            "full_name": "dynamics_400K_ParamsToOuts_1",
            "group": [
                "dynamics",
                "400K",
            ],
            "name": "dynamics_400K_ParamsToOuts_1",
        },
        {
            "changed": False,
            "full_name": "dynamics_ParamsToOuts",
            "group": [
                "dynamics",
            ],
            "name": "dynamics_ParamsToOuts",
        },
        {
            "changed": False,
            "full_name": "dynamics_ParamsToOuts_1",
            "group": [
                "dynamics",
            ],
            "name": "dynamics_ParamsToOuts_1",
        },
    ]

    result = runner.invoke(app, ["list", proj_path.as_posix(), "--json"])
    groups = json.loads(result.stdout)
    assert groups == true_groups

    assert result.exit_code == 0

    result = runner.invoke(app, ["list", proj_path.as_posix()])
    assert result.exit_code == 0

    outs = """
📁 No Group
├── ParamsToOuts ✅
└── ParamsToOuts_1 ✅
📁 dynamics
├── dynamics_ParamsToOuts ✅
├── dynamics_ParamsToOuts_1 ✅
└── 📁 400K
    ├── dynamics_400K_ParamsToOuts ✅
    ├── dynamics_400K_ParamsToOuts_1 ✅
    └── 📁 B
        ├── dynamics_400K_B_ParamsToOuts ✅
        └── dynamics_400K_B_ParamsToOuts_1 ✅
"""
    assert result.stdout in outs
