"""Collection of common fixtures
References
----------
https://docs.pytest.org/en/6.2.x/fixture.html#scope-sharing-fixtures-across-classes-modules-packages-or-session
"""
import os
import pathlib
import shutil
import subprocess

import dvc.cli
import git
import pytest


@pytest.fixture
def proj_path(tmp_path, request) -> pathlib.Path:
    """temporary directory for testing DVC calls

    Parameters
    ----------
    tmp_path
    request: https://docs.pytest.org/en/6.2.x/reference.html#std-fixture-request

    Returns
    -------
    path to temporary directory

    """
    shutil.copy(request.module.__file__, tmp_path)
    os.chdir(tmp_path)
    git.Repo.init()
    dvc.cli.main(["init"])

    return tmp_path
