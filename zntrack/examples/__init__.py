"""Collection of simple Example Nodes"""
from zntrack import Node, zn


class InputToOutput(Node):
    inputs = zn.params()
    outputs = zn.outs()

    def run(self):
        self.outputs = self.inputs


class InputToMetric(InputToOutput):
    outputs = zn.metrics()


class AddInputs(Node):
    a = zn.params()
    b = zn.params()
    result = zn.metrics()

    def run(self):
        self.result = self.a + self.b
