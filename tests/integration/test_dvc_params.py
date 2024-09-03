import pathlib

import pytest
import yaml

import zntrack
from zntrack.config import DVC_FILE_PATH


class SingleNode(zntrack.Node):
    params_file: pathlib.Path | list[pathlib.Path] = zntrack.params_path()

    def run(self):
        pass


def test_dvc_params(proj_path):
    """Test serialized data as parameters"""
    params = {"a": 100}
    file = pathlib.Path("my_params.yaml")

    file.write_text(yaml.safe_dump(params))
    with zntrack.Project() as proj:
        SingleNode(params_file=file)
    proj.build()
    proj.run()

    assert SingleNode.from_rev().params_file == file
    dvc_file = yaml.safe_load(DVC_FILE_PATH.read_text())
    assert [{"my_params.yaml": None}] == dvc_file["stages"]["SingleNode"]["params"]


def test_dvc_params_list(proj_path):
    """Test serialized data as parameters"""
    params = {"a": 100}
    file1 = pathlib.Path("my_params1.yaml")
    file2 = pathlib.Path("my_params2.yaml")

    file1.write_text(yaml.safe_dump(params))
    file2.write_text(yaml.safe_dump(params))

    with zntrack.Project() as proj:
        SingleNode(params_file=[file1, file2])
    proj.build()
    proj.run()

    assert SingleNode.from_rev().params_file == [file1, file2]
    dvc_file = yaml.safe_load(DVC_FILE_PATH.read_text())
    assert [{"my_params1.yaml": None}, {"my_params2.yaml": None}] == dvc_file["stages"][
        "SingleNode"
    ]["params"]


class MixedParams(zntrack.Node):
    params_file1: list[pathlib.Path] = zntrack.params_path()
    params_file2: pathlib.Path = zntrack.params_path()
    params: dict = zntrack.params()

    def run(self):
        pass


def test_dvc_mixed_params_list(proj_path):
    """Test serialized data as parameters"""
    params = {"a": 100}
    file1 = pathlib.Path("my_params1.yaml")
    file2 = pathlib.Path("my_params2.yaml")

    file1.write_text(yaml.safe_dump(params))
    file2.write_text(yaml.safe_dump(params))

    with zntrack.Project() as proj:
        MixedParams(params_file1=[file1, file2], params_file2=file1, params={"a": 100})
    proj.build()

    assert MixedParams.from_rev().params_file1 == [file1, file2]
    assert MixedParams.from_rev().params_file2 == file1
    assert MixedParams.from_rev().params == {"a": 100}
    dvc_file = yaml.safe_load(DVC_FILE_PATH.read_text())
    assert [
        "MixedParams",
        {"my_params1.yaml": None},
        {"my_params2.yaml": None},
    ] == dvc_file["stages"]["MixedParams"]["params"]


def test_dvc_params_error(proj_path):
    """Test serialized data as parameters"""
    with pytest.raises(ValueError):
        with zntrack.Project() as proj:
            SingleNode(params_file={"a": 100})
        proj.build()
