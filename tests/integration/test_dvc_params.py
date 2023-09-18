import pathlib

import pytest
import yaml

from zntrack import Node, Project, dvc, zn
from zntrack.utils import config


class SingleNode(Node):
    params_file = dvc.params()

    def run(self):
        pass


def test_dvc_params(proj_path):
    """Test serialized data as parameters"""
    params = {"a": 100}
    file = pathlib.Path("my_params.yaml")

    file.write_text(yaml.safe_dump(params))
    with Project() as proj:
        SingleNode(params_file=file)
    proj.run()

    assert SingleNode.from_rev().params_file == file
    dvc_file = yaml.safe_load(config.files.dvc.read_text())
    assert [{"my_params.yaml": None}] == dvc_file["stages"]["SingleNode"]["params"]


def test_dvc_params_list(proj_path):
    """Test serialized data as parameters"""
    params = {"a": 100}
    file1 = pathlib.Path("my_params1.yaml")
    file2 = pathlib.Path("my_params2.yaml")

    file1.write_text(yaml.safe_dump(params))
    file2.write_text(yaml.safe_dump(params))

    with Project() as proj:
        SingleNode(params_file=[file1, file2])
    proj.run()

    assert SingleNode.from_rev().params_file == [file1, file2]
    dvc_file = yaml.safe_load(config.files.dvc.read_text())
    assert [{"my_params1.yaml": None}, {"my_params2.yaml": None}] == dvc_file["stages"][
        "SingleNode"
    ]["params"]


class MixedParams(Node):
    params_file1 = dvc.params()
    params_file2 = dvc.params()
    params = zn.params()

    def run(self):
        pass


def test_dvc_mixed_params_list(proj_path):
    """Test serialized data as parameters"""
    params = {"a": 100}
    file1 = pathlib.Path("my_params1.yaml")
    file2 = pathlib.Path("my_params2.yaml")

    file1.write_text(yaml.safe_dump(params))
    file2.write_text(yaml.safe_dump(params))

    with Project() as proj:
        MixedParams(params_file1=[file1, file2], params_file2=file1, params={"a": 100})
    proj.run()

    assert MixedParams.from_rev().params_file1 == [file1, file2]
    assert MixedParams.from_rev().params_file2 == file1
    assert MixedParams.from_rev().params == {"a": 100}
    dvc_file = yaml.safe_load(config.files.dvc.read_text())
    assert [
        "MixedParams",
        {"my_params1.yaml": None},
        {"my_params2.yaml": None},
    ] == dvc_file["stages"]["MixedParams"]["params"]


def test_dvc_params_error(proj_path):
    """Test serialized data as parameters"""
    with pytest.raises(ValueError):
        with Project() as proj:
            SingleNode(params_file={"a": 100})
        proj.build()
