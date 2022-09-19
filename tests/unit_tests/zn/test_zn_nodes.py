import pytest

from zntrack import Node, zn


def test_ExampleNodeWithDefaults():
    with pytest.raises(ValueError):
        # zn.Nodes does not support default values because they can be mutable
        _ = zn.Nodes("any default value")


class ExampleCls:
    example = zn.Nodes()


def test_none_node():
    node = ExampleCls()
    with pytest.raises(ValueError):
        node.example = "not a node"


class ParamsNode(Node):
    pass


class ParamsNodeWithHash(Node):
    _hash = zn.Hash()


class ExampleNode(Node):
    example = zn.Nodes()


def test_require_hash():
    with pytest.raises(ValueError):
        _ = ExampleNode(example=ParamsNode())

    _ = ExampleNode(example=ParamsNodeWithHash())

    with pytest.raises(ValueError):
        _ = ExampleNode(example=[ParamsNodeWithHash()])
    with pytest.raises(ValueError):
        _ = ExampleNode(example=(ParamsNodeWithHash(),))

    _ = ExampleNode(example=None)  # allow None type
