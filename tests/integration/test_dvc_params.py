import pathlib

import pytest
import yaml

from zntrack import Node, dvc, zn


class SingleNode(Node):
    params_file = dvc.params()

    def run(self):
        pass


def test_dvc_params(proj_path):
    """Test serialized data as parameters"""
    params = {"a": 100}
    file = pathlib.Path("my_params.yaml")

    file.write_text(yaml.safe_dump(params))

    SingleNode(params_file=file).write_graph()

    assert SingleNode.from_rev().params_file == file
    dvc_file = yaml.safe_load(pathlib.Path("dvc.yaml").read_text())
    assert ["my_params.yaml"] == dvc_file["stages"]["SingleNode"]["params"]


def test_dvc_params_list(proj_path):
    """Test serialized data as parameters"""
    params = {"a": 100}
    file1 = pathlib.Path("my_params1.yaml")
    file2 = pathlib.Path("my_params2.yaml")

    file1.write_text(yaml.safe_dump(params))
    file2.write_text(yaml.safe_dump(params))

    SingleNode(params_file=[file1, file2]).write_graph()

    assert SingleNode.from_rev().params_file == [file1, file2]
    dvc_file = yaml.safe_load(pathlib.Path("dvc.yaml").read_text())
    assert ["my_params1.yaml", "my_params2.yaml"] == dvc_file["stages"]["SingleNode"][
        "params"
    ]


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

    MixedParams(
        params_file1=[file1, file2], params_file2=file1, params={"a": 100}
    ).write_graph()

    assert MixedParams.from_rev().params_file1 == [file1, file2]
    assert MixedParams.from_rev().params_file2 == file1
    assert MixedParams.from_rev().params == {"a": 100}
    dvc_file = yaml.safe_load(pathlib.Path("dvc.yaml").read_text())
    assert ["MixedParams", "my_params1.yaml", "my_params2.yaml"] == dvc_file["stages"][
        "MixedParams"
    ]["params"]


def test_dvc_params_error(proj_path):
    """Test serialized data as parameters"""
    with pytest.raises(ValueError):
        SingleNode(params_file={"a": 100}).write_graph()
