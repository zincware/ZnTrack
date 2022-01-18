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


def test_update_config_file_json():
    open_mock = mock_open(
        read_data=json.dumps(
            {"Node1": {"param1": 1, "param2": 2}, "Node2": {"param1": 3, "param2": 4}}
        )
    )

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        file_io.update_config_file(
            file=pathlib.Path("params.json"),
            node_name="Node1",
            value_name="param2",
            value=42,
        )
    open_mock().write.assert_called_once_with(
        json.dumps(
            {"Node1": {"param1": 1, "param2": 42}, "Node2": {"param1": 3, "param2": 4}},
            indent=4,
        )
    )


def test_update_config_file_new_param():
    open_mock = mock_open(
        read_data=json.dumps(
            {"Node1": {"param1": 1, "param2": 2}, "Node2": {"param1": 3, "param2": 4}}
        )
    )

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        file_io.update_config_file(
            file=pathlib.Path("params.json"),
            node_name="Node1",
            value_name="param3",
            value=3,
        )
    open_mock().write.assert_called_once_with(
        json.dumps(
            {
                "Node1": {"param1": 1, "param2": 2, "param3": 3},
                "Node2": {"param1": 3, "param2": 4},
            },
            indent=4,
        )
    )


def test_update_config_file_new_node():
    open_mock = mock_open(
        read_data=json.dumps(
            {"Node1": {"param1": 1, "param2": 2}, "Node2": {"param1": 3, "param2": 4}}
        )
    )

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        file_io.update_config_file(
            file=pathlib.Path("params.json"),
            node_name="Node3",
            value_name="param1",
            value=1,
        )
    open_mock().write.assert_called_once_with(
        json.dumps(
            {
                "Node1": {"param1": 1, "param2": 2},
                "Node2": {"param1": 3, "param2": 4},
                "Node3": {"param1": 1},
            },
            indent=4,
        )
    )


def test_update_config_file_yaml():
    open_mock = mock_open(
        read_data=yaml.safe_dump(
            {"Node1": {"param1": 1, "param2": 2}, "Node2": {"param1": 3, "param2": 4}}
        )
    )

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        file_io.update_config_file(
            file=pathlib.Path("params.yaml"),
            node_name="Node1",
            value_name="param2",
            value=42,
        )
    open_mock().write.assert_called_once_with(
        yaml.safe_dump(
            {"Node1": {"param1": 1, "param2": 42}, "Node2": {"param1": 3, "param2": 4}},
            indent=4,
        )
    )
