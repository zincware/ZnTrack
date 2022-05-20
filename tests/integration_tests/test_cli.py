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
    assert pathlib.Path("main.py").is_file()
    assert pathlib.Path("README.md").is_file()


def test_init_gitignore(proj_path):
    subprocess.check_call(["zntrack", "init", "--gitignore"])

    assert pathlib.Path("src").is_dir()
    assert (pathlib.Path("src") / "__init__.py").is_file()
    assert pathlib.Path(".git").is_dir()
    assert pathlib.Path(".dvc").is_dir()
    assert pathlib.Path(".gitignore").is_file()
    assert pathlib.Path("main.py").is_file()
    assert pathlib.Path("README.md").is_file()


@pytest.mark.parametrize("force", (True, False))
def test_init_force(proj_path, force):
    pathlib.Path("file.txt").touch()

    if force:
        subprocess.check_call(["zntrack", "init", "--force"])
        assert pathlib.Path("src").is_dir()
        assert (pathlib.Path("src") / "__init__.py").is_file()
        assert pathlib.Path(".git").is_dir()
        assert pathlib.Path(".dvc").is_dir()
        assert pathlib.Path("main.py").is_file()
        assert pathlib.Path("README.md").is_file()
    else:
        subprocess.check_call(["zntrack", "init"])
        assert not pathlib.Path("src").exists()
        assert not pathlib.Path(".git").exists()
        assert not pathlib.Path(".dvc").exists()
        assert not pathlib.Path("main.py").exists()
        assert not pathlib.Path("README.md").exists()
