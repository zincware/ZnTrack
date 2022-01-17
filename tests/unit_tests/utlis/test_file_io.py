import json
import pathlib
from unittest.mock import mock_open, patch

import yaml

from zntrack.utils import file_io


def test_save_file_json():
    open_mock = mock_open(read_data=None)

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        file_io.write_file(pathlib.Path("example.json"), {"a": "b"})

        # use to check the calls
        # assert open_mock.mock_calls == {}

        args, kwargs = open_mock.call_args
        assert args[0] == pathlib.Path("example.json")

        open_mock().write.assert_called_once_with(json.dumps({"a": "b"}, indent=4))


def test_save_file_yaml():
    open_mock = mock_open(read_data=None)

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        file_io.write_file(pathlib.Path("example.yaml"), {"a": "b"})

        args, kwargs = open_mock.call_args
        assert args[0] == pathlib.Path("example.yaml")
        open_mock().write.assert_called_once_with(yaml.safe_dump({"a": "b"}, indent=4))


def test_save_file_yml():
    open_mock = mock_open(read_data=None)

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        file_io.write_file(pathlib.Path("example.yml"), {"a": "b"})

        args, kwargs = open_mock.call_args
        assert args[0] == pathlib.Path("example.yml")
        open_mock().write.assert_called_once_with(yaml.safe_dump({"a": "b"}, indent=4))


def test_read_file_json():
    open_mock = mock_open(read_data=json.dumps({"a": "b"}))

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        assert file_io.read_file(pathlib.Path("example.json")) == {"a": "b"}

        args, kwargs = open_mock.call_args
        assert args[0] == pathlib.Path("example.json")


def test_read_file_yaml():
    open_mock = mock_open(read_data=yaml.safe_dump({"a": "b"}))

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        assert file_io.read_file(pathlib.Path("example.yaml")) == {"a": "b"}

        open_mock.assert_called_with(pathlib.Path("example.yaml"), "r")


def test_read_file_yml():
    open_mock = mock_open(read_data=yaml.safe_dump({"a": "b"}))

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        assert file_io.read_file(pathlib.Path("example.yml")) == {"a": "b"}

        open_mock.assert_called_with(pathlib.Path("example.yml"), "r")
