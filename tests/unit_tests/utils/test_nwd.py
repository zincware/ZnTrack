import os
import pathlib

import pytest

from zntrack import utils
from zntrack.utils.nwd import move_nwd, replace_nwd_placeholder


def test_nwd():
    assert str(utils.nwd) == "$nwd$"
    assert utils.nwd / "test.txt" == pathlib.Path("$nwd$", "test.txt")
    assert f"{utils.nwd}/test.txt" == "$nwd$/test.txt"
    assert os.path.join(utils.nwd, "test.txt") == os.path.join("$nwd$", "test.txt")


def test_replace_nwd_placeholder():
    assert replace_nwd_placeholder(utils.nwd / "test.txt", "node") == pathlib.Path(
        "node", "test.txt"
    )
    assert replace_nwd_placeholder(
        utils.nwd / "test.txt", pathlib.Path("node", "nodename")
    ) == pathlib.Path("node", "nodename", "test.txt")

    assert replace_nwd_placeholder(
        [utils.nwd / "test1.txt", utils.nwd / "test2.txt"], "node"
    ) == [pathlib.Path("node", "test1.txt"), pathlib.Path("node", "test2.txt")]

    assert replace_nwd_placeholder(
        [f"{utils.nwd}/test1.txt", f"{utils.nwd}/test2.txt"], "node"
    ) == ["node/test1.txt", "node/test2.txt"]

    assert replace_nwd_placeholder(
        [f"{utils.nwd}/test1.txt", f"{utils.nwd}/test2.txt"], pathlib.Path("node")
    ) == ["node/test1.txt", "node/test2.txt"]

    assert replace_nwd_placeholder(
        (f"{utils.nwd}/test1.txt", f"{utils.nwd}/test2.txt"), pathlib.Path("node")
    ) == ("node/test1.txt", "node/test2.txt")

    # Test the return value if nothing is to be replaced.

    assert replace_nwd_placeholder(
        pathlib.Path("node") / "test.txt", "node"
    ) == pathlib.Path("node", "test.txt")

    assert replace_nwd_placeholder("my_string", "node") == "my_string"
    assert replace_nwd_placeholder(["my_string_a", "my_string_b"], "node") == [
        "my_string_a",
        "my_string_b",
    ]

    assert replace_nwd_placeholder(["node/test1.txt", "node/test2.txt"], "node") == [
        "node/test1.txt",
        "node/test2.txt",
    ]

    assert replace_nwd_placeholder(["$nwd$/test1.txt", "node/test2.txt"], "node") == [
        "node/test1.txt",
        "node/test2.txt",
    ]

    assert replace_nwd_placeholder(["node/test1.txt", "$nwd$/test2.txt"], "node") == [
        "node/test1.txt",
        "node/test2.txt",
    ]

    # mixed type

    assert replace_nwd_placeholder(
        ["$nwd$/test1.txt", utils.nwd / "test2.txt"], "node"
    ) == ["node/test1.txt", pathlib.Path("node/test2.txt")]

    with pytest.raises(ValueError):
        replace_nwd_placeholder(5, node_working_directory="tmp")

    assert replace_nwd_placeholder(None, node_working_directory="tmp") is None


def test_replace_nwd_single():
    """Replace 'nwd' without __truediv__."""
    assert replace_nwd_placeholder(
        utils.nwd, pathlib.Path("node", "nodename")
    ) == pathlib.Path("node", "nodename")
    assert replace_nwd_placeholder(
        "$nwd$", pathlib.Path("node", "nodename")
    ) == pathlib.Path("node", "nodename")


def test_move_nwd(tmp_path):
    os.chdir(tmp_path)
    directory = tmp_path / "test"
    directory.mkdir()
    (directory / "test.txt").write_text("Foo bar")
    destination = tmp_path / "new"
    move_nwd(directory, destination)
    assert not directory.exists()
    assert destination.exists()
    assert (destination / "test.txt").read_text() == "Foo bar"
