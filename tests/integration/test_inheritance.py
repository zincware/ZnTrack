import typing as t

import pytest

import zntrack
from zntrack import Node, Project


class InputsOutputs(Node):
    inputs: t.Any = zntrack.params()
    outputs: t.Any = zntrack.outs()


class WriteData(InputsOutputs):
    def run(self):
        self.outputs = self.inputs


class WriteDataWithInit(InputsOutputs):
    # def __init__(self, inputs=None, **kwargs):
    #     super().__init__(inputs=inputs, **kwargs)
    #     # this calls the auto_init of the subclass which demands the inputs argument!

    def run(self):
        self.outputs = self.inputs


class InOutsWInit(Node):
    inputs: t.Any = zntrack.params()
    outputs: t.Any = zntrack.outs()

    # def __init__(self, inputs=None, **kwargs):
    #     super().__init__(**kwargs)
    #     self.inputs = inputs


class WriteDataParentInit(InOutsWInit):
    def run(self):
        self.outputs = self.inputs


class WriteDataParentInitWithInit(InOutsWInit):
    # def __init__(self, inputs=None, **kwargs):
    #     super().__init__(**kwargs)
    #     self.inputs = inputs

    def run(self):
        self.outputs = self.inputs


@pytest.mark.parametrize(
    "cls",
    (WriteData, WriteDataWithInit, WriteDataParentInit, WriteDataParentInitWithInit),
)
def test_simple_inheritance(proj_path, cls):
    with Project() as project:
        node = cls(inputs="HelloWorld")
    project.run()
    # node.load()
    assert node.outputs == "HelloWorld"
    assert cls.from_rev().outputs == "HelloWorld"


class WriteCustomData(InputsOutputs):
    custom: str = zntrack.params()

    def run(self):
        self.outputs = f"{self.inputs} {self.custom}"


def test_WriteCustomData(proj_path):
    with Project() as project:
        node = WriteCustomData(inputs="Hello", custom="World")
    project.run()
    # node.load()
    assert node.outputs == "Hello World"
    assert WriteCustomData.from_rev().outputs == "Hello World"
