import dataclasses
import functools
import os
import pathlib
import subprocess
import typing as t

import znfields

import zntrack
from zntrack.config import (
    FIELD_TYPE,
    NOT_AVAILABLE,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_CACHE,
)
from zntrack.plugins import ZnTrackPlugin, base_getter, plugin_getter


def _text_getter(self: zntrack.Node, name: str):
    with self.state.fs.open(self.nwd / f"{name}.txt", mode="r") as f:
        return f.read()


class TextPlugin(ZnTrackPlugin):
    def getter(self, field: dataclasses.Field) -> t.Any:
        if field.metadata.get(FIELD_TYPE) == "TextPlugin.text":
            return base_getter(self.node, field.name, _text_getter)

        return PLUGIN_EMPTY_RETRUN_VALUE

    def save(self, field: dataclasses.Field) -> None:
        if field.metadata.get(FIELD_TYPE) == "TextPlugin.text":
            if not pathlib.Path(self.node.nwd).exists():
                pathlib.Path(self.node.nwd).mkdir(parents=True)
            with open(self.node.nwd / f"{field.name}.txt", "w") as f:
                f.write(getattr(self.node, field.name))

    def convert_to_zntrack_json(self, graph=None):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_dvc_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_params_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE


@functools.wraps(znfields.field)
def text(*, cache: bool = True, **kwargs):
    kwargs["metadata"] = kwargs.get("metadata", {})
    kwargs["metadata"][FIELD_TYPE] = "TextPlugin.text"
    kwargs["metadata"][ZNTRACK_CACHE] = cache
    return znfields.field(default=NOT_AVAILABLE, getter=plugin_getter, **kwargs)


class TextNode(zntrack.Node):
    user: str = zntrack.params()

    comment: str = text()

    def run(self):
        self.comment = f"Hello, {self.user}!"


def test_simple_text(proj_path):
    os.environ["ZNTRACK_PLUGINS"] = (
        "tests.integration.test_options_custom.TextPlugin,zntrack.plugins.dvc_plugin.DVCPlugin"
    )
    try:
        with zntrack.Project() as proj:
            node = TextNode(user="Max")

        proj.build()
        subprocess.run(["dvc", "repro"], cwd=proj_path, check=True)

        with open(node.nwd / "comment.txt") as f:
            comment = f.read()

        assert comment == "Hello, Max!"

        assert node.comment == "Hello, Max!"

        node = node.from_rev()

        assert node.comment == "Hello, Max!"
    finally:
        del os.environ["ZNTRACK_PLUGINS"]
