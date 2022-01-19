"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
import os
import shutil

from zntrack import Node, ZnTrackProject, dvc, zn


class CreateNumbers(Node):
    number = zn.outs()

    def run(self):
        self.number = 42


class AddOne(Node):
    inp = dvc.deps(CreateNumbers.load())
    number = zn.outs()

    def run(self):
        self.number = self.inp.number + 1


class SubtractOne(Node):
    inp = dvc.deps(CreateNumbers.load())
    number = zn.outs()

    def run(self):
        self.number = self.inp.number - 1


class Summation(Node):
    """Stage that is actually tested, containing the multiple dependencies"""

    inp = dvc.deps([AddOne.load(), SubtractOne.load()])
    number = zn.outs()

    def run(self):
        self.number = self.inp[0].number + self.inp[1].number


class SummationTuple(Node):
    """Stage that is actually tested, containing the multiple dependencies

    Additionally testing for tuple conversion here!
    """

    inp = dvc.deps((AddOne.load(), SubtractOne.load()))
    number = zn.outs()

    def run(self):
        self.number = self.inp[0].number + self.inp[1].number


def test_repro(tmp_path):
    """Test that a single DVC.deps() can take a list of dependencies"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    project = ZnTrackProject()
    project.create_dvc_repository()

    CreateNumbers().write_graph()
    AddOne().write_graph()
    SubtractOne().write_graph()
    Summation().write_graph()
    SummationTuple().write_graph()

    project.repro()

    assert Summation.load().number == 84
    assert SummationTuple.load().number == 84
