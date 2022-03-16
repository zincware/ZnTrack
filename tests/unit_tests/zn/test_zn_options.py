import dataclasses
import json
import pathlib

import pytest
import znjson

from zntrack import zn
from zntrack.zn.dependencies import NodeAttribute, getdeps
from zntrack.zn.split_option import combine_values, split_value


class ExampleClass:
    module = None  # must mock the module here
    is_loaded = False
    method = zn.Method()


def test_zn_method_get():
    class ExampleMethod:
        pass

    example = ExampleClass()
    example.method = ExampleMethod()

    assert isinstance(example.__dict__["method"], ExampleMethod)
    assert example.method.znjson_zn_method

    assert isinstance(ExampleClass.method.__get__(None, None), zn.Method)


class ExamplePlots:
    module = None
    is_loaded = False
    node_name = "ExamplePlots"
    plots = zn.plots()


def test_zn_plots():
    example = ExamplePlots()
    # test save and load if there is nothing to save or load
    assert ExamplePlots.plots.save(example) is None
    with pytest.raises(FileNotFoundError):
        _ = ExamplePlots.plots.get_data_from_files(example)


@dataclasses.dataclass
class ExampleDataClass:
    a: int = 5
    b: int = 7

    # make it a zn.Method
    znjson_zn_method = True

    def __eq__(self, other):
        return (other.a == self.a) and (other.b == self.b)


def test_split_value():
    serialized_value = json.loads(json.dumps(ExampleDataClass(), cls=znjson.ZnEncoder))

    params_data, zntrack_data = split_value(serialized_value)
    assert zntrack_data == {"_type": "zn.method", "value": {"module": "test_zn_options"}}
    assert params_data == {"_cls": "ExampleDataClass", "a": 5, "b": 7}

    # and now test the same thing but serialize a list
    serialized_value = json.loads(json.dumps([ExampleDataClass()], cls=znjson.ZnEncoder))
    params_data, zntrack_data = split_value(serialized_value)
    assert zntrack_data == [
        {"_type": "zn.method", "value": {"module": "test_zn_options"}}
    ]
    assert params_data == ({"_cls": "ExampleDataClass", "a": 5, "b": 7},)


def test_combine_values():
    zntrack_data = {"_type": "zn.method", "value": {"module": "test_zn_options"}}
    params_data = {"_cls": "ExampleDataClass", "a": 5, "b": 7}

    assert combine_values(zntrack_data, params_data) == ExampleDataClass()

    # try older data structure
    zntrack_data = {
        "_type": "zn.method",
        "value": {
            "module": "test_zn_options",
            "cls": "ExampleDataClass",
        },
    }
    params_data = {"a": 5, "b": 7}
    assert combine_values(zntrack_data, params_data) == ExampleDataClass()

    # try older data structure
    zntrack_data = {
        "_type": "zn.method",
        "value": {
            "module": "test_zn_options",
            "name": "ExampleDataClass",
        },
    }
    params_data = {"a": 5, "b": 7}
    assert combine_values(zntrack_data, params_data) == ExampleDataClass()


def test_split_value_path():
    path = pathlib.Path("my_path")
    serialized_value = json.loads(json.dumps(path, cls=znjson.ZnEncoder))

    params_data, zntrack_data = split_value(serialized_value)

    assert params_data == "my_path"
    assert zntrack_data == {"_type": "pathlib.Path"}

    new_path = combine_values(zntrack_data, params_data)
    # TODO change order to be consistent with split_values
    assert new_path == path


class ExampleNode:
    module = "module"
    node_name = "node01"
    affected_files = ["a", "b"]


def test_getdeps():
    assert getdeps(ExampleNode(), "my_attr") == NodeAttribute(
        module="module",
        cls="ExampleNode",
        name="node01",
        attribute="my_attr",
        affected_files=["a", "b"],
    )
