import pytest

from zntrack.core.functions.decorator import NodeConfig


def test_not_supported_outs():
    with pytest.raises(ValueError):
        NodeConfig(outs=25)
    with pytest.raises(ValueError):
        NodeConfig(outs=[25])
    with pytest.raises(ValueError):
        NodeConfig(outs={"path": 25})

    assert NodeConfig(outs="path").outs == "path"


def test_not_supported_params():
    with pytest.raises(ValueError):
        NodeConfig(params=25)
    with pytest.raises(ValueError):
        NodeConfig(params=[25])


def test_supported_params():
    assert NodeConfig(params={"name": "John"}).params["name"] == "John"
