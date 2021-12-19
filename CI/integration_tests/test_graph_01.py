"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Simple test for graph execution
"""
import os
import shutil

import numpy as np

from zntrack import Node, ZnTrackProject, dvc


@Node()
class ComputeA:
    """Node stage A"""

    def __init__(self):
        self.inp = dvc.params()
        self.out = dvc.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp).item()


@Node()
class ComputeB:
    """Node stage B"""

    def __init__(self):
        self.inp = dvc.params()
        self.out = dvc.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(3, self.inp).item()


@Node()
class ComputeAB:
    """Node stage AB, depending on A&B"""

    def __init__(self):
        self.a = dvc.deps(ComputeA(id_=0))
        self.b = dvc.deps(ComputeB(id_=0))
        self.out = dvc.result()

        self.param = dvc.params()

    def __call__(self):
        self.param = "default"

    def run(self):
        a = ComputeA(id_=0).out
        b = ComputeB(id_=0).out
        self.out = a + b


@Node(name="Stage_A")
class ComputeANamed:
    """Node stage A"""

    def __init__(self):
        self.inp = dvc.params()
        self.out = dvc.result()

    def __call__(self, inp):
        self.inp = inp

    def run(self):
        self.out = np.power(2, self.inp).item()


@Node(name="Stage_AB")
class ComputeABNamed:
    """Node stage AB, depending on A&B with a custom stage name"""

    def __init__(self):
        self.a: ComputeANamed = dvc.deps(ComputeANamed(id_=0))
        self.b: ComputeB = dvc.deps(ComputeB(id_=0))
        self.out = dvc.result()

        self.param = dvc.params()

    def __call__(self):
        self.param = "default"

    def run(self):
        self.out = self.a.out + self.b.out


def test_stage_addition(tmp_path):
    """Check that the dvc repro works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeAB()
    ab()

    project.run()
    project.repro()
    finished_stage = ComputeAB(load=True)
    assert finished_stage.out == 31


def test_stage_addition_named(tmp_path):
    """Check that the dvc repro works with named stages"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeANamed()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeABNamed()
    ab()

    project.repro()
    finished_stage = ComputeABNamed(id_=0)
    assert finished_stage.out == 31


def test_stage_addition_run(tmp_path):
    """Check that the PyTracks run method works"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeA()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeAB()
    ab()

    a.run()
    b.run()
    ab.run()

    finished_stage = ComputeAB(id_=0)
    assert finished_stage.out == 31


def test_stage_addition_named_run(tmp_path):
    """Check that the PyTracks run method works with named stages"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.name = "test01"
    project.create_dvc_repository()

    a = ComputeANamed()
    a(2)
    b = ComputeB()
    b(3)
    ab = ComputeABNamed()
    ab()

    ComputeANamed(load=True).run()
    ComputeB(load=True).run()
    ComputeABNamed(load=True).run()

    finished_stage = ComputeABNamed(load=True)
    assert finished_stage.out == 31


def test_named_single_stage(tmp_path):
    """Test a single named stage"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    project = ZnTrackProject()
    project.create_dvc_repository()

    a = ComputeANamed()
    a(2)

    project.repro()

    assert ComputeANamed(load=True).out == 4
