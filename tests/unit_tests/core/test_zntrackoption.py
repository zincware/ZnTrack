import os
import pathlib
from unittest.mock import mock_open, patch

from zntrack import utils, zn


class ExampleMethod:
    def run(self):
        return 42


class ExampleNode:
    node_name = None
    module = "module"
    method = zn.Method(ExampleMethod())


def test_method_filename():
    assert ExampleNode.method.get_filename(ExampleNode()) == (
        utils.Files.params,
        utils.Files.zntrack,
    )


def test_method_save(tmp_path):
    os.chdir(tmp_path)

    open_mock = mock_open(read_data="{}")

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        ExampleNode.method.save(ExampleNode())

    # TODO assert some things here, for the params.yaml and zntrack.json writing
