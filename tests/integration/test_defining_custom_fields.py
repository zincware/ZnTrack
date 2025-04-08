import pathlib

import h5py
import numpy as np
import numpy.testing as npt

import zntrack
from zntrack.config import NOT_AVAILABLE, FieldTypes

CWD = pathlib.Path(__file__).parent.resolve()


def _h5data_getter(self: zntrack.Node, name: str, suffix: str):
    file = (self.nwd / name).with_suffix(suffix)
    with self.state.fs.open(file, mode="rb") as f:
        return h5py.File(f, "r")["data"][()]


# TODO: if ZNTRACK_FIELD_SUFFIX is None (not, not defined!) then
#   assume a directory is being saved there for DVC


def _h5data_save_func(self: zntrack.Node, name: str, suffix: str):
    file = (self.nwd / name).with_suffix(suffix)
    with h5py.File(file, "w") as f:
        f.create_dataset("data", data=getattr(self, name))


def h5data(*, cache: bool = True, independent: bool = False, **kwargs):
    return zntrack.field(
        cache=cache,
        independent=independent,
        field_type=FieldTypes.OUTS,
        load_fn=_h5data_getter,
        dump_fn=_h5data_save_func,
        suffix=".h5",
        repr=False,
        init=False,
        default=NOT_AVAILABLE,
        **kwargs,
    )


class NumpyNode(zntrack.Node):
    content: np.ndarray = h5data()

    def run(self):
        self.content = np.arange(9).reshape(3, 3)


def test_np_node(proj_path):
    with zntrack.Project() as project:
        node = NumpyNode()
    project.repro()

    npt.assert_array_equal(node.content, np.arange(9).reshape(3, 3))
