import os
import pathlib
import shutil
import subprocess

import pytest


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    return tmp_path


def test_init(proj_path):
    subprocess.check_call(["zntrack", "init"])

    assert pathlib.Path("src").is_dir()
    assert (pathlib.Path("src") / "__init__.py").is_file()
    assert pathlib.Path(".git").is_dir()
    assert pathlib.Path(".dvc").is_dir()


def test_init_gitignore(proj_path):
    subprocess.check_call(["zntrack", "init", "--gitignore"])

    assert pathlib.Path("src").is_dir()
    assert (pathlib.Path("src") / "__init__.py").is_file()
    assert pathlib.Path(".git").is_dir()
    assert pathlib.Path(".dvc").is_dir()
    assert pathlib.Path(".gitignore").is_file()
