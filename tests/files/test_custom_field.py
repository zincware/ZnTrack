import functools
import json
import pathlib

import yaml
import znfields
import h5py
import numpy as np
import numpy.testing as npt

import zntrack
from zntrack import Node
from zntrack.config import (
    NOT_AVAILABLE,
    ZNTRACK_CACHE,
    ZNTRACK_FIELD_DUMP,
    ZNTRACK_FIELD_LOAD,
    ZNTRACK_FIELD_SUFFIX,
    ZNTRACK_INDEPENDENT_OUTPUT_TYPE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.plugins import base_getter, plugin_getter

CWD = pathlib.Path(__file__).parent.resolve()


def _h5data_getter(self: Node, name: str, suffix: str):
    file = (self.nwd / name).with_suffix(suffix)
    with self.state.fs.open(file, mode="rb") as f:
        self.__dict__[name] = h5py.File(f, "r")["data"][()]


def _h5data_save_func(self: Node, name: str, suffix: str):
    file = (self.nwd / name).with_suffix(suffix)
    with h5py.File(file, "w") as f:
        f.create_dataset("data", data=getattr(self, name))


def h5data(*, cache: bool = True, independent: bool = False, **kwargs) -> znfields.field:
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = functools.partial(
        base_getter, func=_h5data_getter
    )
    kwargs["metadata"][ZNTRACK_FIELD_DUMP] = _h5data_save_func
    kwargs["metadata"][ZNTRACK_FIELD_SUFFIX] = ".h5"
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )


class TextNode(Node):
    content: np.ndarray = h5data()

    def run(self):
        self.content = np.arange(9).reshape(3, 3)


def test_text_node(proj_path):

    with zntrack.Project() as project:
        node = TextNode()
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

    # I know this is file testing but this should be fast
    project.repro(build=False)
    
    npt.assert_array_equal(node.content, np.arange(9).reshape(3, 3))
