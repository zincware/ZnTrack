"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Check that all dependencies work as expected
"""
import subprocess

from zntrack import Node, dvc, zn
from pathlib import Path
import pytest
import shutil
import os


@Node()
class DVCOuts:
    data_file: Path = dvc.outs(Path("data"))

    def run(self):
        self.data_file.write_text("Lorem Ipsum")


@Node()
class ZnOuts:
    data: str = zn.outs()

    def run(self):
        self.data = "Lorem Ipsum"


@Node()
class DVCZnOuts:
    data_file: Path = dvc.outs(Path("data"))
    data: str = zn.outs()

    def __call__(self, *args, **kwargs):
        pass

    def run(self):
        self.data_file.write_text("Lorem Ipsum")
        self.data = "Lorem Ipsum"


@Node()
class DependenciesCollector:
    dependencies = dvc.deps()

    def __call__(self, dependencies):
        self.dependencies = dependencies

    def run(self):
        pass


@Node()
class DepsCollwOuts:
    dependencies = dvc.deps()
    outs: Path = dvc.outs(Path("lorem.txt"))

    def __call__(self, dependencies):
        self.dependencies = dependencies

    def run(self):
        self.outs.write_text("Lorem Ipsum")


@pytest.fixture()
def dvc_repo_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


def test_dvc_outs(dvc_repo_path):
    os.chdir(dvc_repo_path)

    dvc_outs = DVCOuts()
    dvc_outs()

    dependencies_collector = DependenciesCollector()
    dependencies_collector(dependencies=DVCOuts(load=True))

    subprocess.check_call(["dvc", "repro"])

    assert (
        DependenciesCollector(load=True).dependencies.data_file.read_text()
        == "Lorem Ipsum"
    )


def test_zn_outs(dvc_repo_path):
    os.chdir(dvc_repo_path)

    zn_outs = ZnOuts()
    zn_outs()

    dependencies_collector = DependenciesCollector()
    dependencies_collector(dependencies=ZnOuts(load=True))

    subprocess.check_call(["dvc", "repro"])

    assert DependenciesCollector(load=True).dependencies.data == "Lorem Ipsum"


def test_dvc_zn_outs(dvc_repo_path):
    os.chdir(dvc_repo_path)

    dvc_zn_outs = DVCZnOuts()
    dvc_zn_outs()

    dependencies_collector = DependenciesCollector()
    dependencies_collector(dependencies=DVCZnOuts(load=True))

    subprocess.check_call(["dvc", "repro"])

    assert (
        DependenciesCollector(load=True).dependencies.data_file.read_text()
        == "Lorem Ipsum"
    )

    assert DependenciesCollector(load=True).dependencies.data == "Lorem Ipsum"


def test_expand_dependencies(dvc_repo_path):
    os.chdir(dvc_repo_path)

    dvc_zn_outs = DVCZnOuts()
    dvc_zn_outs()

    dependencies_collector = DependenciesCollector(name="Collector01")
    dependencies_collector(dependencies=DVCZnOuts(load=True))

    dependencies_collector = DependenciesCollector(name="Collector02")
    dependencies_collector(
        dependencies=DependenciesCollector(name="Collector01", load=True)
    )

    subprocess.check_call(["dvc", "repro"])


def test_exp_deps_w_outs(dvc_repo_path):
    """test_expand_dependencies_with_outs"""
    os.chdir(dvc_repo_path)

    dvc_zn_outs = DVCZnOuts()
    dvc_zn_outs()

    dependencies_collector = DepsCollwOuts(name="Collector01")
    dependencies_collector(dependencies=DVCZnOuts(load=True))

    dependencies_collector = DepsCollwOuts(name="Collector02")
    dependencies_collector(dependencies=DepsCollwOuts(name="Collector01", load=True))

    subprocess.check_call(["dvc", "repro"])
