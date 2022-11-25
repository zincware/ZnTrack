import json
import os
import pathlib
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
import znjson

from zntrack.utils import utils


def test_cwd_temp_dir():
    new_dir = utils.cwd_temp_dir(required_files=[__file__])
    assert pathlib.Path(new_dir.name) == pathlib.Path(os.getcwd())
    assert next(pathlib.Path(new_dir.name).glob("*.py")).name == "test_utils.py"
    os.chdir("..")
    new_dir.cleanup()


def test_decode_dict_path():
    path = pathlib.Path("test.txt")
    dict_string = json.dumps(path, cls=znjson.ZnEncoder)
    loaded_dict = json.loads(dict_string)
    assert loaded_dict == {"_type": "pathlib.Path", "value": "test.txt"}
    assert utils.decode_dict(loaded_dict) == path
    assert utils.decode_dict(None) is None


class EmptyCls:
    pass


class ClsWithPostInit:
    def post_init(self):
        self.post_init = True
        self.text = f"{self.foo} {self.bar}"


def test_module_handler():
    my_mock = MagicMock
    my_mock.__module__ = "custom_module"
    assert utils.module_handler(my_mock) == "custom_module"

    my_mock.__module__ = "__main__"
    with patch.object(sys, "argv", ["ipykernel_launcher"]):
        assert utils.module_handler(my_mock) == "__main__"

    with patch.object(sys, "argv", ["pytest-runner"]):
        assert utils.module_handler(my_mock) == "pytest-runner"


def test_check_type():
    assert utils.check_type("str", str)
    assert not utils.check_type(["str"], str)
    assert utils.check_type(["str"], str, allow_iterable=True)

    assert utils.check_type(25, (int, str))
    assert not utils.check_type([25, "str"], (int, str))
    assert utils.check_type([25, "str"], (int, str), allow_iterable=True)

    assert utils.check_type(["str"], list)
    assert utils.check_type(None, str, allow_none=True)
    assert not utils.check_type([None], str, allow_none=True)
    assert utils.check_type([None], str, allow_none=True, allow_iterable=True)

    assert utils.check_type({"key": "val"}, str, allow_dict=True)
    assert not utils.check_type({"key": "val"}, str)
    assert utils.check_type({"a": {"b": "c"}}, str, allow_dict=True)


def test_python_interpreter():
    assert utils.get_python_interpreter() in ["python", "python3"]


def test_module_to_path():
    assert utils.module_to_path("src.module") == pathlib.Path("src", "module.py")


@pytest.mark.parametrize(
    ("cmd", "error"), [(["init"], False), (["add", "file.txt"], True)]
)
def test_run_dvc_command(tmp_path, cmd: list, error: bool):
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    if error:
        with pytest.raises(utils.DVCProcessError):
            utils.run_dvc_cmd(cmd)
    else:
        assert utils.run_dvc_cmd(cmd) == 0
