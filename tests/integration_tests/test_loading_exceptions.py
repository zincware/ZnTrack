import pytest

import zntrack
from zntrack import Node, dvc, zn


class WriteNumber(Node):
    input = zn.params()
    output = zn.outs()

    def run(self):
        self.output = self.input


class WriteNumberDVC(Node):
    input = zn.params()
    output = dvc.outs("test.txt")

    def run(self):
        with open(self.output) as f:
            f.write("Hello World")


@pytest.mark.parametrize("model", [WriteNumber, WriteNumberDVC])
def test_GraphNotAvailableError(model):
    node_obj = model.load()
    with pytest.raises(zntrack.exceptions.GraphNotAvailableError):
        _ = node_obj.input

    with pytest.raises(zntrack.exceptions.GraphNotAvailableError):
        # TODO is this really GraphNotAvailable or DataNotAvailable?
        _ = node_obj.output


def test_DataNotAvailableError(proj_path):
    node_obj = WriteNumber(input=5)
    node_obj.write_graph()

    node_obj = WriteNumber.load()
    assert node_obj.input == 5
    with pytest.raises(zntrack.exceptions.DataNotAvailableError):
        _ = node_obj.output
