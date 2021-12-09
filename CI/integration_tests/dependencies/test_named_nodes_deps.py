"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Test dependencies for named nodes
"""
import os
import shutil
import subprocess
from typing import List

from zntrack import Node, dvc, zn


@Node()
class GetNumber:
    input_number = dvc.params()
    output_number = zn.outs()

    def __call__(self, *args, **kwargs):
        pass

    def run(self):
        self.output_number = self.input_number


@Node()
class FindMax:
    deps = dvc.deps()
    maximum = zn.outs()

    def __call__(self, dependencies: List[GetNumber]):
        self.deps = dependencies

    def run(self):
        self.maximum = 0
        for get_number in self.deps:
            if get_number.output_number > self.maximum:
                self.maximum = get_number.output_number


def test_project(tmp_path):
    """Check that dependencies on named nodes work correclty"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    all_numbers = []

    max_n = 5

    for number in range(max_n):
        get_number = GetNumber(name=f"node_{number}")
        get_number.input_number = number
        get_number()

        all_numbers.append(get_number)

    FindMax()(all_numbers)

    subprocess.check_call(["dvc", "repro"])

    assert FindMax(load=True).maximum == max_n - 1
