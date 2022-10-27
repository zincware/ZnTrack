import pytest

from zntrack import examples


@pytest.mark.parametrize("ExampleNode", (examples.InputToOutput, examples.InputToMetric))
def test_InputToOutput(proj_path, ExampleNode):
    node = ExampleNode(inputs=25)
    node.write_graph()
    node.run_and_save()

    assert node.load().inputs == 25
    assert node.load().outputs == 25


def test_AddInputs(proj_path):
    node = examples.AddInputs(a=5, b=10)
    node.write_graph()
    node.run_and_save()

    assert node.load().a == 5
    assert node.load().b == 10
    assert node.load().result == 15
