import pytest

from zntrack.core.base import DVCOptions


@pytest.fixture()
def dvc_options():
    return DVCOptions(
        no_commit=True,
        external=True,
        always_changed=True,
        no_exec=True,
        force=True,
        no_run_cache=True,
    )


def test_dvc_arguments(dvc_options):
    assert dvc_options.dvc_arguments == [
        "--no-commit",
        "--external",
        "--always-changed",
        "--no-exec",
        "--force",
        "--no-run-cache",
    ]


def test_no_exec_warning(dvc_options):
    dvc_options.no_exec = False
    assert dvc_options.dvc_arguments == [
        "--no-commit",
        "--external",
        "--always-changed",
        "--force",
        "--no-run-cache",
    ]
