"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
from zntrack import Node, DVC, ZnTrackProject
import os
import shutil


@Node()
class CreateNumbers:
    number = DVC.result()

    def run(self):
        self.number = 42


@Node()
class AddOne:
    inp = DVC.deps(CreateNumbers(load=True))
    number = DVC.result()

    def run(self):
        self.number = self.inp.number + 1


@Node()
class SubtractOne:
    inp = DVC.deps(CreateNumbers(load=True))
    number = DVC.result()

    def run(self):
        self.number = self.inp.number - 1


@Node()
class Summation:
    inp = DVC.deps([AddOne(load=True), SubtractOne(load=True)])
    number = DVC.result()

    def run(self):
        self.number = self.inp[0].number + self.inp[1].number


@Node()
class SummationTuple:
    inp = DVC.deps((AddOne(load=True), SubtractOne(load=True)))
    number = DVC.result()

    def run(self):
        self.number = self.inp[0].number + self.inp[1].number


def test_repro(tmp_path):
    """Test that a single DVC.deps() can take a list of dependencies"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    project = ZnTrackProject()
    project.create_dvc_repository()

    CreateNumbers()()
    AddOne()()
    SubtractOne()()
    Summation()()
    SummationTuple()()

    project.repro()

    assert Summation(load=True).number == 84
    assert SummationTuple(load=True).number == 84
