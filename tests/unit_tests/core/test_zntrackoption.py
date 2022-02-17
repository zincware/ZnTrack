import pytest

from zntrack import utils, zn


def test_zn_outs_error():
    with pytest.raises(ValueError):

        class ExampleOutsDefault:
            node_name = "test"
            parameter = zn.outs(default_value="Lorem Ipsum")


class ExampleMethod:
    def run(self):
        return 42


class ExampleNode:
    node_name = None
    module = "module"
    method = zn.Method(ExampleMethod())


def test_method_filename():
    assert ExampleNode.method.get_filename(ExampleNode()) == (
        utils.Files.params,
        utils.Files.zntrack,
    )
