import pytest

from zntrack import Node, zn


class InOuts(Node):
    inputs = zn.params()
    outputs = zn.outs()


class WriteData(InOuts):
    def run(self):
        self.outputs = self.inputs


class WriteDataWithInit(InOuts):
    def __init__(self, inputs=None, **kwargs):
        super().__init__(inputs=inputs, **kwargs)
        # this calls the auto_init of the subclass which demands the inputs argument!

    def run(self):
        self.outputs = self.inputs


class InOutsWInit(Node):
    inputs = zn.params()
    outputs = zn.outs()

    def __init__(self, inputs=None, **kwargs):
        super().__init__(**kwargs)
        self.inputs = inputs


class WriteDataParentInit(InOutsWInit):
    def run(self):
        self.outputs = self.inputs


class WriteDataParentInitWithInit(InOutsWInit):
    def __init__(self, inputs=None, **kwargs):
        super().__init__(**kwargs)
        self.inputs = inputs

    def run(self):
        self.outputs = self.inputs


@pytest.mark.parametrize(
    "MyNode",
    (WriteData, WriteDataWithInit, WriteDataParentInit, WriteDataParentInitWithInit),
)
def test_simple_inheritance(proj_path, MyNode):
    node = MyNode(inputs="HelloWorld")
    node.write_graph(run=True)
    node.load()
    assert node.outputs == "HelloWorld"
    assert MyNode.from_rev().outputs == "HelloWorld"


class WriteCustomData(InOuts):
    custom = zn.params()

    def run(self):
        self.outputs = f"{self.inputs} {self.custom}"


def test_WriteCustomData(proj_path):
    node = WriteCustomData(inputs="Hello", custom="World")
    node.write_graph(run=True)
    node.load()
    assert node.outputs == "Hello World"
    assert WriteCustomData.from_rev().outputs == "Hello World"
