import json
import pathlib

import znjson

import zntrack.zn.dependencies


class MockNode:
    affected_files = [pathlib.Path("data.json")]

    @classmethod
    def load(cls, *args, **kwargs):
        return cls()


def test_RawNodeAttributeConverter():
    node_attribute = zntrack.zn.dependencies.NodeAttribute(
        module=MockNode.__module__,
        cls=MockNode.__name__,
        name="MyNode",
        attribute="my_node",
    )

    data = json.dumps(
        node_attribute,
        cls=znjson.ZnEncoder.from_converters(
            zntrack.zn.dependencies.RawNodeAttributeConverter, add_default=True
        ),
    )
    assert json.loads(data) == {
        "_type": "NodeAttribute",
        "value": {
            "attribute": "my_node",
            "cls": MockNode.__name__,
            "module": MockNode.__module__,
            "name": "MyNode",
        },
    }

    new_node_attribute = json.loads(
        data,
        cls=znjson.ZnDecoder.from_converters(
            zntrack.zn.dependencies.RawNodeAttributeConverter, add_default=True
        ),
    )

    assert new_node_attribute == node_attribute
    assert node_attribute.affected_files == [pathlib.Path("data.json")]
