import json
import pathlib

import numpy as np
import yaml

import zntrack
from zntrack.config import NOT_AVAILABLE, FieldTypes
from zntrack.fields import field

CWD = pathlib.Path(__file__).parent.resolve()


def _h5data_getter(self: zntrack.Node, name: str, suffix: str):
    raise NotImplementedError


def _h5data_save_func(self: zntrack.Node, name: str, suffix: str):
    raise NotImplementedError


def h5data(*, cache: bool = True, independent: bool = False, **kwargs):
    return field(
        cache=cache,
        independent=independent,
        field_type=FieldTypes.OUTS,
        load_fn=_h5data_getter,
        dump_fn=_h5data_save_func,
        suffix=".h5",
        repr=False,
        default=NOT_AVAILABLE,
        **kwargs,
    )


class TextNode(zntrack.Node):
    content: np.ndarray = h5data()

    def run(self):
        self.content = np.arange(9).reshape(3, 3)


def test_text_node(proj_path):
    with zntrack.Project() as project:
        TextNode()
    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "custom_field.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "custom_field.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "custom_field.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()
