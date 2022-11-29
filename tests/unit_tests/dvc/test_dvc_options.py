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
