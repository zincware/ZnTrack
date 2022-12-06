import dataclasses

import pytest
import yaml
import znjson

from zntrack import config, zn
from zntrack.core.base import Node


class NodeViaParams(Node):
    _hash = zn.Hash()
    param1 = zn.params()
    param2 = zn.params()

    def run(self):
        pass


class ExampleNode(Node):
    params1: NodeViaParams = zn.Nodes()
    params2: NodeViaParams = zn.Nodes()

    outs = zn.outs()

    def run(self):
        self.outs = self.params1.param1 + self.params2.param2


class NodeWithPlots(Node):
    _hash = zn.Hash()
    plots = zn.plots()
    factor: float = zn.params()

    def run(self):
        pass


class ExampleUsesPlots(Node):
    node_with_plots: NodeWithPlots = zn.Nodes()
    param: int = zn.params()
    out = zn.outs()

    def run(self):
        self.out = self.node_with_plots.factor * self.param


def test_ExampleNode(proj_path):
    ExampleNode(
        params1=NodeViaParams(param1="Hello", param2="World"),
        params2=NodeViaParams(param1="Lorem", param2="Ipsum"),
    ).write_graph(run=True)

    example_node = ExampleNode.load()

    assert example_node.params1.param1 == "Hello"
    assert example_node.params1.param2 == "World"
    assert example_node.params2.param1 == "Lorem"
    assert example_node.params2.param2 == "Ipsum"
    assert example_node.outs == "HelloIpsum"


class SingleExampleNode(Node):
    params1 = zn.Nodes()
    outs = zn.outs()

    def run(self):
        self.outs = "Lorem Ipsum"


def test_SingleExampleNode(proj_path):
    SingleExampleNode(params1=None).write_graph(run=True)

    assert SingleExampleNode.load().outs == "Lorem Ipsum"


class NodeNodeParams(Node):
    deps: NodeViaParams = zn.deps()
    node: NodeViaParams = zn.Nodes()
    _hash = zn.Hash()

    def run(self):
        pass


class ExampleNode2(Node):
    params1: NodeNodeParams = zn.Nodes()
    params2 = zn.Nodes()

    def run(self):
        pass


@pytest.mark.parametrize("dvc_api", (True, False))
def test_depth_graph(proj_path, dvc_api):
    with config.updated_config(dvc_api=dvc_api):
        node_1 = NodeViaParams(param1="Lorem", param2="Ipsum", name="Node1")
        node_1.write_graph(run=True)  # defined as dependency, so it must run first.

        node_2 = NodeViaParams(param1="Lorem", param2="Ipsum")

        node_3 = NodeNodeParams(deps=node_1, node=node_2, name="Node3")

        node_4 = ExampleNode2(params1=node_3, params2=None)

        node_4.write_graph(run=True)

        node_4 = ExampleNode2.load()

        assert node_4.params1.deps.param1 == "Lorem"
        assert node_4.params1.node.param2 == "Ipsum"

        assert node_4.params1.node_name == "ExampleNode2_params1"
        assert node_4.params1.deps.node_name == "Node1"
        assert node_4.params1.node.node_name == "ExampleNode2_params1_node"


class NodeWithOuts(Node):
    input = zn.params()
    factor = zn.params()
    output = zn.outs()
    _hash = zn.Hash()

    def run(self):
        self.output = self.input * self.factor


def test_NodeWithOuts(proj_path):
    node_1 = SingleExampleNode(params1=NodeWithOuts(factor=2, input=None))
    node_1.write_graph(run=True)

    assert SingleExampleNode.load().params1.factor == 2


@dataclasses.dataclass
class Parameter:
    value: int = 0


class NodeWithParameter(Node):
    parameter = zn.params(Parameter())
    _hash = zn.Hash()


class MoreNode(Node):
    node: NodeWithParameter = zn.Nodes()


class ParameterConverter(znjson.ConverterBase):
    level = 100
    representation = "parameter"
    instance = Parameter

    def _encode(self, obj: Parameter) -> dict:
        return dataclasses.asdict(obj)

    def _decode(self, value: dict) -> Parameter:
        return Parameter(**value)


def test_DataclassNode(proj_path):
    znjson.register(ParameterConverter)

    node_w_params = NodeWithParameter(parameter=Parameter(value=42))
    node_w_params.write_graph()

    node = MoreNode(node=NodeWithParameter(parameter=Parameter(value=10)))
    node.write_graph()

    node_w_params = node_w_params.load()
    assert node_w_params.parameter.value == 42

    node = node.load()
    assert node.node.parameter.value == 10

    znjson.deregister(ParameterConverter)


@pytest.mark.parametrize("node_name", ("ExampleUsesPlots", "test12"))
def test_ExampleUsesPlots(proj_path, node_name):
    node = ExampleUsesPlots(
        node_with_plots=NodeWithPlots(factor=2.5), param=2.0, name=node_name
    )
    assert node.node_with_plots._is_attribute is True
    assert node.node_with_plots.node_name == f"{node_name}_node_with_plots"
    assert len(node.node_with_plots._descriptor_list) == 2

    node.write_graph()
    ExampleUsesPlots[node_name].run_and_save()

    assert ExampleUsesPlots[node_name].out == 2.5 * 2.0

    # Just checking if changing the parameters works as well
    with open("params.yaml", "r") as file:
        parameters = yaml.safe_load(file)
    parameters[f"{node_name}_node_with_plots"]["factor"] = 1.0
    with open("params.yaml", "a") as file:
        yaml.safe_dump(parameters, file)

    assert ExampleUsesPlots[node_name].node_with_plots.factor == 1.0


class NodeAsDataClass(Node):
    _hash = zn.Hash()
    param1 = zn.params()
    param2 = zn.params()
    param3 = zn.params()


class UseNodeAsDataClass(Node):
    params: NodeAsDataClass = zn.Nodes()
    output = zn.outs()

    def run(self):
        self.output = self.params.param1 + self.params.param2 + self.params.param3


def test_UseNodeAsDataClass(proj_path):
    node = UseNodeAsDataClass(params=NodeAsDataClass(param1=1, param2=10, param3=100))
    node.write_graph(run=True)

    node = UseNodeAsDataClass.load()
    assert node.output == 111
    assert node.params.param1 == 1
    assert node.params.param2 == 10
    assert node.params.param3 == 100
