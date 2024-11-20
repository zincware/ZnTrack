import functools
import json
import pathlib

import h5py
import numpy as np
import numpy.testing as npt
import yaml
import znfields

import zntrack
from zntrack.fields import field
from zntrack.config import ZnTrackOptionEnum, NOT_AVAILABLE
import dataclasses

CWD = pathlib.Path(__file__).parent.resolve()


def _h5data_getter(self: zntrack.Node, name: str, suffix: str):
    # file = (self.nwd / name).with_suffix(suffix)
    # with self.state.fs.open(file, mode="rb") as f:
    #     self.__dict__[name] = h5py.File(f, "r")["data"][()]
    raise NotImplementedError


# TODO: test without getter  / save_func - it should not be called when purely writing!
# TODO: test with getter in a different test
# TODO: try to somehow replicate the ipsuite issue...
# TODO: check if you can simpify the fields defintion by removing cache,
#   and the need to use functools.partial, base better, plugin_getter, etc.
# should only be ZNTRACK_OPTION, ZNTRACK_FIELD_LOAD, ZNTRACK_FIELD_DUMP, ZNTRACK_FIELD_SUFFIX
# TODO: if ZNTRACK_FIELD_SUFFIX is None (not, not defined!) then
#   assume a directory is being saved there for DVC
# TODO: fix -> znfields.field return type, try dataclass field? Fix updstream


def _h5data_save_func(self: zntrack.Node, name: str, suffix: str):
    # file = (self.nwd / name).with_suffix(suffix)
    # with h5py.File(file, "w") as f:
    #     f.create_dataset("data", data=getattr(self, name))
    raise NotImplementedError


def h5data(
    *, cache: bool = True, independent: bool = False, **kwargs
):
    return field(
        cache=cache,
        independent=independent,
        zntrack_option=ZnTrackOptionEnum.OUTS,
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

    # # I know this is file testing but this should be fast
    # project.repro(build=False)

    # npt.assert_array_equal(node.content, np.arange(9).reshape(3, 3))
