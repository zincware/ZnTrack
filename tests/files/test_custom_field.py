import functools
import json
import pathlib

import yaml
import znfields

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


def _text_getter(self: Node, name: str, suffix: str):
    with self.state.fs.open((self.nwd / name).with_suffix(suffix), mode="r") as f:
        self.__dict__[name] = f.read()


def _text_save_func(self: Node, name: str, suffix: str):
    (self.nwd / name).with_suffix(suffix).write_text(getattr(self, name))


def text(*, cache: bool = True, independent: bool = False, **kwargs) -> znfields.field:
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][ZNTRACK_OPTION] = ZnTrackOptionEnum.OUTS
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    kwargs["metadata"][ZNTRACK_INDEPENDENT_OUTPUT_TYPE] = independent
    kwargs["metadata"][ZNTRACK_FIELD_LOAD] = functools.partial(
        base_getter, func=_text_getter
    )
    kwargs["metadata"][ZNTRACK_FIELD_DUMP] = _text_save_func
    kwargs["metadata"][ZNTRACK_FIELD_SUFFIX] = ".txt"
    return znfields.field(
        default=NOT_AVAILABLE, getter=plugin_getter, **kwargs, init=False
    )


class TextNode(Node):
    content: str = text()

    def run(self):
        self.content = "Hello, World!"


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
    assert node.content == "Hello, World!"
