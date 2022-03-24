import json
import pathlib
from unittest.mock import MagicMock, call, mock_open, patch

import pytest
import yaml

from zntrack import dvc, zn
from zntrack.core.base import (
    LoadViaGetItem,
    Node,
    get_auto_init_signature,
    update_dependency_options,
)


class ExampleDVCOutsNode(Node):
    outs = dvc.outs("example.dat")


def test_node_module():
    example = ExampleDVCOutsNode()
    assert example.module == "test_core_base"

    example._module = "src.base"
    assert example.module == "src.base"


class ExampleFullNode(Node):
    params = zn.params(10)
    zn_outs = zn.outs()
    dvc_outs = dvc.outs("file.txt")
    deps = dvc.deps("deps.inp")

    def run(self):
        self.zn_outs = "outs"


@pytest.mark.parametrize("run", (True, False))
def test_save(run):
    zntrack_mock = mock_open(read_data="{}")
    params_mock = mock_open(read_data="{}")
    zn_outs_mock = mock_open(read_data="{}")

    example = ExampleFullNode()

    def pathlib_open(*args, **kwargs):
        if args[0] == pathlib.Path("zntrack.json"):
            return zntrack_mock(*args, **kwargs)
        elif args[0] == pathlib.Path("params.yaml"):
            return params_mock(*args, **kwargs)
        elif args[0] == pathlib.Path("nodes/ExampleFullNode/outs.json"):
            return zn_outs_mock(*args, **kwargs)
        else:
            raise ValueError(args)

    with patch.object(pathlib.Path, "open", pathlib_open):
        if run:
            example.run()
            example.save(results=True)
            assert zn_outs_mock().write.mock_calls == [
                call(json.dumps({"zn_outs": "outs"}, indent=4))
            ]
        else:
            example.save()
            assert zntrack_mock().write.mock_calls == [
                call(
                    json.dumps(
                        {"ExampleFullNode": {"dvc_outs": "file.txt"}},
                        indent=4,
                    )
                ),
                call(
                    json.dumps(
                        {"ExampleFullNode": {"deps": "deps.inp"}},
                        indent=4,
                    )
                ),
            ]
            assert params_mock().write.mock_calls == [
                call(yaml.safe_dump({"ExampleFullNode": {"params": 10}}, indent=4))
            ]


def test__load():
    zntrack_mock = mock_open(
        read_data=json.dumps(
            {"ExampleFullNode": {"dvc_outs": "file_.txt", "deps": "deps_.inp"}},
            indent=4,
        )
    )
    params_mock = mock_open(read_data=yaml.safe_dump({"ExampleFullNode": {"params": 42}}))
    zn_outs_mock = mock_open(read_data=json.dumps({"zn_outs": "outs_"}))

    example = ExampleFullNode()

    def pathlib_open(*args, **kwargs):
        if args[0] == pathlib.Path("zntrack.json"):
            return zntrack_mock(*args, **kwargs)
        elif args[0] == pathlib.Path("params.yaml"):
            return params_mock(*args, **kwargs)
        elif args[0] == pathlib.Path("nodes/ExampleFullNode/outs.json"):
            return zn_outs_mock(*args, **kwargs)
        else:
            raise ValueError(args)

    with patch.object(pathlib.Path, "open", pathlib_open):
        example.update_options()
        assert example.dvc_outs == "file_.txt"
        assert example.deps == "deps_.inp"
        assert example.params == 42
        assert example.zn_outs == "outs_"
        assert example.is_loaded


class CorrectNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.test_name = self.node_name


class InCorrectNode(Node):
    def __init__(self):
        super().__init__()
        self.test_name = self.node_name


def test_load():
    default_correct_node = CorrectNode.load()
    assert default_correct_node.node_name == CorrectNode.__name__

    default_incorrect_node = InCorrectNode.load()
    assert default_incorrect_node.node_name == InCorrectNode.__name__

    correct_node = CorrectNode.load(name="Test")
    assert correct_node.node_name == "Test"
    assert correct_node.test_name == correct_node.node_name

    incorrect_node = InCorrectNode.load(name="Test")
    assert incorrect_node.node_name == "Test"
    assert incorrect_node.test_name != incorrect_node.node_name


class RunTestNode(Node):
    outs = zn.outs()

    def run(self):
        self.outs = 42


def test_run_and_save():
    open_mock = mock_open(read_data="{}")

    example = RunTestNode()

    def pathlib_open(*args, **kwargs):
        return open_mock(*args, **kwargs)

    with patch.object(pathlib.Path, "open", pathlib_open):
        example.run_and_save()

        assert example.outs == 42

    assert open_mock().write.mock_calls == [
        call(json.dumps({"outs": 42}, indent=4)),
    ]


class WrongInit(Node):
    def __init__(self, non_default, **kwargs):
        super().__init__(**kwargs)


def test_WrongInit():
    """Test that a TypeError occurs if any value it not set to default in __init__"""
    with pytest.raises(TypeError):
        WrongInit.load()


def test_update_dependency_options():
    """Test update_dependency_options calls

    I'm not sure if this is the supposed way to use patch / MagicMock but it works
    """

    with patch(f"{__name__}.MagicMock", spec=Node):
        magic_mock = MagicMock()
        update_dependency_options(magic_mock)
        assert magic_mock.update_options.called

    with patch(f"{__name__}.MagicMock", spec=Node):
        magic_mock = MagicMock()
        update_dependency_options([magic_mock])
        assert magic_mock.update_options.called


class ZnTrackOptionCollection:
    param1: dict = zn.params()
    param2: list = zn.params([1, 2])
    param3 = zn.params()

    out1: str = dvc.outs()
    out2: pathlib.Path = dvc.outs()
    out3 = dvc.outs()

    result: int = zn.outs()
    result2 = zn.outs()

    no_option: int = 5
    no_option2 = 42


def test_get_auto_init_signature():
    zn_option_names, signature_params = get_auto_init_signature(ZnTrackOptionCollection)

    assert zn_option_names == [
        "param1",
        "param2",
        "param3",
        "out1",
        "out2",
        "out3",
    ]

    assert signature_params[0].name == "param1"
    assert signature_params[0].annotation == dict

    assert signature_params[2].name == "param3"
    assert signature_params[2].annotation is None

    assert signature_params[-1].name == "out3"


class NodeMock(metaclass=LoadViaGetItem):
    def load(self):
        pass


@pytest.mark.parametrize(
    ("key", "called"),
    [
        ("node", {"name": "node"}),
        ({"name": "node"}, {"name": "node"}),
        ({"name": "node", "lazy": True}, {"name": "node", "lazy": True}),
    ],
)
def test_LoadViaGetItem(key, called):
    with patch.object(NodeMock, "load") as mock:
        NodeMock[key]

    mock.assert_called_with(**called)


def test_matmul_not_supported():
    with pytest.raises(ValueError):
        # must be str
        RunTestNode @ 25

    with pytest.raises(ValueError):
        RunTestNode() @ 25

    with patch("zntrack.core.base.getdeps") as mock:
        # must patch the correct namespace
        # https://stackoverflow.com/a/16134754/10504481
        NodeMock @ "string"
        RunTestNode @ "outs"
        RunTestNode() @ "outs"

    assert mock.call_count == 3
