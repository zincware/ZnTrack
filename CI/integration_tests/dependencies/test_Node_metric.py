"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
import subprocess

from zntrack import Node, dvc, zn
from pathlib import Path
import json
import shutil
import os


@Node()
class ComputeMeaning:
    """BasicTest class"""

    metric: Path = dvc.metrics(Path("my_metric.json"))

    def run(self):
        """Run method of the Node test instance"""
        self.metric.write_text(json.dumps({"val1": 42}))


@Node()
class PrintMeaning:
    computation: ComputeMeaning = dvc.deps(ComputeMeaning(load=True))

    def run(self):
        print(self.computation.metric.read_text())


# The same but with zn
@Node()
class ComputeMeaningZn:
    """BasicTest class"""

    metric = zn.metrics()

    def run(self):
        """Run method of the Node test instance"""
        self.metric = {"my_metric": 42}


@Node()
class PrintMeaningZn:
    computation: ComputeMeaningZn = dvc.deps(ComputeMeaningZn(load=True))
    result = zn.outs()

    def run(self):
        self.result = self.computation.metric["my_metric"]


def test_project(tmp_path):
    """Check that metric files are added to the dependencies when depending on a Node"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    ComputeMeaning()()
    PrintMeaning()()

    subprocess.check_call(["dvc", "repro"])

    print_meaning = PrintMeaning(load=True)
    print_meaning.zntrack.update_dvc()

    assert ComputeMeaning(load=True).metric in print_meaning.zntrack.dvc.deps


def test_with_zn(tmp_path):
    """Check the same test but using zn.metric instead"""
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    ComputeMeaningZn()()
    PrintMeaningZn()()

    subprocess.check_call(["dvc", "repro"])

    assert PrintMeaningZn(load=True).result == 42
