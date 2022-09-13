"""Additional tests for getdeps can be found in test_node_to_node_dependencies"""
import pathlib
import subprocess

import numpy as np
import pytest

from zntrack import getdeps, utils, zn
from zntrack.core import ZnTrackOption
from zntrack.core.base import Node
from zntrack.zn.dependencies import NodeAttribute, get_origin


class SeedNumbers(Node):
    shape: tuple = zn.params()
    number: np.ndarray = zn.outs()

    def run(self):
        self.number = np.random.random(size=self.shape)


class RandomLikeDeps(Node):
    inputs: np.ndarray = zn.deps()
    number = zn.outs()

    def run(self):
        self.number = np.random.random(size=self.inputs.shape)


def test_getdeps_via_matmul(proj_path):
    steps = 3
    sd = SeedNumbers(shape=(5, 5))
    sd.write_graph()

    for step in range(steps):
        if step == 0:
            RandomLikeDeps(
                inputs=SeedNumbers @ "number", name=f"rld_{step}"
            ).write_graph()
        else:
            RandomLikeDeps(
                inputs=RandomLikeDeps[f"rld_{step - 1}"] @ "number",
                name=f"rld_{step}",
            ).write_graph()

    subprocess.check_call(["dvc", "repro"])

    for step in range(steps):
        assert RandomLikeDeps[f"rld_{step}"].number.shape == (5, 5)


@pytest.mark.parametrize("steps", (1, 5))
def test_stacked_name_getdeps(proj_path, steps):
    sd = SeedNumbers(shape=(5, 5))
    sd.write_graph()

    for step in range(steps):
        if step == 0:
            RandomLikeDeps(
                inputs=getdeps(SeedNumbers, "number"), name=f"rld_{step}"
            ).write_graph()
        else:
            RandomLikeDeps(
                inputs=getdeps(RandomLikeDeps[f"rld_{step - 1}"], "number"),
                name=f"rld_{step}",
            ).write_graph()

    subprocess.check_call(["dvc", "repro"])

    for step in range(steps):
        assert RandomLikeDeps[f"rld_{step}"].number.shape == (5, 5)


class ToString(ZnTrackOption):
    dvc_option = "outs"
    zn_type = utils.ZnTypes.RESULTS

    def get_filename(self, instance) -> pathlib.Path:
        """Overwrite filename to csv"""
        return pathlib.Path("nodes", instance.node_name, f"{self.name}.db")

    def save(self, instance):
        """Save value with ase.db.connect"""
        data = self.__get__(instance, self.owner)
        file = self.get_filename(instance)
        file.write_text(str(data))

    def get_data_from_files(self, instance):
        """Load value with ase.db.connect"""
        print(30 * "#" + " LOADING " + 30 * "#")
        file = self.get_filename(instance)
        return file.read_text()


class SeedNumber(Node):
    inputs = zn.params()
    number: str = ToString()

    def run(self):
        self.number = self.inputs


class ModifyNumber(Node):
    inputs = zn.deps()
    outputs = zn.outs()

    def run(self):
        self.outputs = self.inputs

    @property
    def number(self):
        return int(self.outputs)


@pytest.mark.parametrize("steps", (1, 2, 3, 4))
def test_stacked_name_getdeps_1(proj_path, steps):
    sd = SeedNumber(inputs=1)
    sd.write_graph()

    for step in range(steps):
        if step == 0:
            ModifyNumber(inputs=getdeps(sd, "number"), name=f"rld_{step}").write_graph()
        else:
            ModifyNumber(
                inputs=getdeps(ModifyNumber[f"rld_{step - 1}"], "outputs"),
                name=f"rld_{step}",
            ).write_graph()

    subprocess.check_call(["dvc", "repro"])

    for step in range(steps):
        assert ModifyNumber[f"rld_{step}"].outputs == "1"


@pytest.mark.parametrize("steps", (1, 2, 3, 4))
def test_stacked_name_getdeps_2(proj_path, steps):
    sd = SeedNumber(inputs=1)
    sd.write_graph()

    for step in range(steps):
        if step == 0:
            ModifyNumber(inputs=getdeps(sd, "number"), name=f"rld_{step}").write_graph()
        else:
            ModifyNumber(
                inputs=getdeps(ModifyNumber[f"rld_{step - 1}"], "number"),
                name=f"rld_{step}",
            ).write_graph()

    subprocess.check_call(["dvc", "repro"])

    for step in range(1, steps):
        assert ModifyNumber[f"rld_{step}"].outputs == 1

        node_attr = get_origin(ModifyNumber[f"rld_{step}"], "inputs")
        assert isinstance(node_attr, NodeAttribute)
        assert node_attr.name == f"rld_{step - 1}"


def test_get_origin(proj_path):
    sd = SeedNumber(inputs=20)
    sd.write_graph()
    ModifyNumber(inputs=getdeps(sd, "number")).write_graph()

    node_attr = get_origin(ModifyNumber.load(), "inputs")
    assert isinstance(node_attr, NodeAttribute)
    assert node_attr.name == "SeedNumber"


def test_get_origin_lst(proj_path):
    sd = SeedNumber(inputs=20)
    sd.write_graph()
    sd2 = SeedNumber(inputs=10, name="sd2")
    sd2.write_graph()
    ModifyNumber(inputs=[getdeps(sd, "number"), getdeps(sd2, "number")]).write_graph()

    node_attr = get_origin(ModifyNumber.load(), "inputs")
    assert isinstance(node_attr[0], NodeAttribute)
    assert isinstance(node_attr[1], NodeAttribute)
    assert node_attr[0].name == "SeedNumber"
    assert node_attr[1].name == "sd2"


def test_err_get_origin(proj_path):
    sd = SeedNumber(inputs=20)
    sd.write_graph()
    ModifyNumber(inputs=getdeps(sd, "number")).write_graph()

    with pytest.raises(AttributeError):
        get_origin(ModifyNumber.load(), "outputs")

    with pytest.raises(AttributeError):
        get_origin(SeedNumber, "inputs")

    ModifyNumber(inputs=[getdeps(sd, "number"), sd]).write_graph()

    with pytest.raises(AttributeError):
        get_origin(ModifyNumber.load(), "inputs")
