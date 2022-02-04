"""ZnTrack
License
-------
This program and the accompanying materials are made available under the terms
of the Eclipse Public License v2.0 which accompanies this distribution, and is
available at https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0
Copyright Contributors to the Zincwarecode Project.
Contact Information
-------------------
email: zincwarecode@gmail.com
github: https://github.com/zincware
web: https://zincwarecode.com/

Description: Collection of tests to ensure that some files are only changed during
the run method / the node creation.
"""

import os
import pathlib
import shutil
import subprocess

import pytest

from zntrack import dvc, zn
from zntrack.core.base import Node


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class ChangeParamsInRun(Node):
    param = zn.params()

    def run(self):
        self.param = "incorrect param"


def test_ChangeParamsInRun(proj_path):
    ChangeParamsInRun(param="correct param").write_graph(run=True)

    assert ChangeParamsInRun.load().param == "correct param"


class ChangeJsonInRun(Node):
    outs = dvc.outs(pathlib.Path("correct_out.txt"))

    def run(self):
        # need to create the file because DVC will fail otherwise
        self.outs.write_text("Create Correct File")
        self.outs = pathlib.Path("incorrect_out.txt")


def test_ChangeJsonInRun(proj_path):
    ChangeJsonInRun().write_graph(run=True)
    assert ChangeJsonInRun.load().outs == pathlib.Path("correct_out.txt")


class WriteToOutsOutsideRun(Node):
    outs = zn.outs()

    def __init__(self, outs=None, **kwargs):
        super().__init__(**kwargs)
        self.outs = outs

    def run(self):
        self.outs = "correct outs"


def test_WriteToOutsOutsideRun(proj_path):
    WriteToOutsOutsideRun(outs="incorrect outs").run_and_save()
    assert WriteToOutsOutsideRun.load().outs == "correct outs"
    WriteToOutsOutsideRun(outs="incorrect outs").save()
    assert WriteToOutsOutsideRun.load().outs == "correct outs"
