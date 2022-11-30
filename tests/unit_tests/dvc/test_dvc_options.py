"""Tests for 'zntrack.dvc'."""
import pathlib

import pytest

from zntrack import dvc


def test_dvc_deps_type():
    """Test type checking of 'dvc.deps'."""

    class Example:
        deps = dvc.deps()

    node = Example()

    node.deps = "string"
    node.deps = pathlib.Path.cwd()
    node.deps = ["string", pathlib.Path.cwd()]

    node.deps = None
    with pytest.raises(ValueError):
        node.deps = 25


def test_dvc_nwd():
    """Test nwd and serialize=True."""

    class Example:
        nwd = pathlib.Path("nodes", "Example")
        is_loaded = True
        outs = dvc.outs()

    node = Example()
    node.outs = pathlib.Path("$nwd$", "file.txt")

    assert node.outs == pathlib.Path("nodes", "Example", "file.txt")
    assert node.outs == node.nwd / "file.txt"

    assert Example.outs.__get__(node, serialize=True) == pathlib.Path("$nwd$", "file.txt")

    # now with lists
    node.outs = [pathlib.Path("$nwd$", "file.txt")]
    assert node.outs == [pathlib.Path("nodes", "Example", "file.txt")]
    assert node.outs == [node.nwd / "file.txt"]

    assert Example.outs.__get__(node, serialize=True) == [
        pathlib.Path("$nwd$", "file.txt")
    ]
