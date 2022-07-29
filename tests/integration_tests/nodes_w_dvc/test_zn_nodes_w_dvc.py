import os
import pathlib
import shutil
import subprocess

import pytest

from zntrack import Node, dvc, zn


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class WriteOutsNode(Node):
    outs: pathlib.Path = dvc.outs()
    _hash = zn.Hash()

    def run(self):
        self.outs.write_text("Lorem Ipsum")


class UseMethod(Node):
    outs_method: WriteOutsNode = zn.Nodes()

    def run(self):
        self.outs_method.run()


def test_zn_nodes_dvc_outs(proj_path):
    out_file = pathlib.Path("output.txt")
    UseMethod(outs_method=WriteOutsNode(outs=out_file)).write_graph(run=True)

    assert out_file.exists()
