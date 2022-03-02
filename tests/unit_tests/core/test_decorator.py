import pathlib

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


def test_NodeConfig_convert_fields_to_dotdict():
    cfg = NodeConfig(outs="file")
    assert cfg.outs == "file"

    cfg = NodeConfig(outs={"file": "file.txt"})
    cfg.convert_fields_to_dotdict()
    assert cfg.outs.file == "file.txt"
    assert cfg.outs["file"] == "file.txt"

    cfg = NodeConfig(outs={"files": {"data": "datafile.txt"}})
    cfg.convert_fields_to_dotdict()
    assert cfg.outs.files.data == "datafile.txt"

    cfg = NodeConfig(
        outs={"files": {"file": "datafile.txt", "path": pathlib.Path("data.txt")}}
    )
    cfg.convert_fields_to_dotdict()
    assert cfg.outs.files.file == "datafile.txt"
    assert cfg.outs.files.path == pathlib.Path("data.txt")
