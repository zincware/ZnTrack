import os
import pathlib

from zntrack import utils
from zntrack.utils.nwd import replace_nwd_placeholder


def test_nwd():
    assert str(utils.nwd) == "$nwd$"
    assert utils.nwd / "test.txt" == pathlib.Path("$nwd$", "test.txt")
    assert f"{utils.nwd}/test.txt" == "$nwd$/test.txt"
    assert os.path.join(utils.nwd, "test.txt") == os.path.join("$nwd$", "test.txt")


def test_replace_nwd_placeholder():
    assert replace_nwd_placeholder(utils.nwd / "test.txt", "node") == (
        pathlib.Path("node", "test.txt"),
        True,
    )
    assert replace_nwd_placeholder(
        utils.nwd / "test.txt", pathlib.Path("node", "nodename")
    ) == (pathlib.Path("node", "nodename", "test.txt"), True)

    assert replace_nwd_placeholder(
        [utils.nwd / "test1.txt", utils.nwd / "test2.txt"], "node"
    ) == ([pathlib.Path("node", "test1.txt"), pathlib.Path("node", "test2.txt")], True)

    assert replace_nwd_placeholder(
        [f"{utils.nwd}/test1.txt", f"{utils.nwd}/test2.txt"], "node"
    ) == (["node/test1.txt", "node/test2.txt"], True)

    assert replace_nwd_placeholder(
        [f"{utils.nwd}/test1.txt", f"{utils.nwd}/test2.txt"], pathlib.Path("node")
    ) == (["node/test1.txt", "node/test2.txt"], True)

    # Test the return value if nothing is to be replaced.

    assert replace_nwd_placeholder(pathlib.Path("node") / "test.txt", "node") == (
        pathlib.Path("node", "test.txt"),
        False,
    )

    assert replace_nwd_placeholder("my_string", "node") == ("my_string", False)
    assert replace_nwd_placeholder(["my_string_a", "my_string_b"], "node") == (
        ["my_string_a", "my_string_b"],
        False,
    )

    assert replace_nwd_placeholder(["node/test1.txt", "node/test2.txt"], "node") == (
        ["node/test1.txt", "node/test2.txt"],
        False,
    )

    assert replace_nwd_placeholder(["$nwd$/test1.txt", "node/test2.txt"], "node") == (
        ["node/test1.txt", "node/test2.txt"],
        True,
    )

    assert replace_nwd_placeholder(["node/test1.txt", "$nwd$/test2.txt"], "node") == (
        ["node/test1.txt", "node/test2.txt"],
        True,
    )

    # mixed type

    assert replace_nwd_placeholder(
        ["$nwd$/test1.txt", utils.nwd / "test2.txt"], "node"
    ) == (["node/test1.txt", pathlib.Path("node/test2.txt")], True)
