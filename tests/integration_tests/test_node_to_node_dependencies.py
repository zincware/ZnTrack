import os
import shutil
import subprocess
from pathlib import Path

import pytest

from zntrack import dvc, zn
from zntrack.core.base import Node


class DVCOuts(Node):
    data_file: Path = dvc.outs()

    def __init__(self):
        super().__init__()
        self.data_file = Path("data")

    def run(self):
        self.data_file.write_text("Lorem Ipsum")


class ZnOuts(Node):
    data: str = zn.outs()

    def run(self):
        self.data = "Lorem Ipsum"


class DVCZnOuts(Node):
    data_file: Path = dvc.outs()
    data: str = zn.outs()

    def __init__(self):
        super().__init__()
        self.data_file = Path("data")

    def run(self):
        self.data_file.write_text("Lorem Ipsum")
        self.data = "Lorem Ipsum"


class DependenciesCollector(Node):
    dependencies = dvc.deps()

    def __init__(self, dependencies=None):
        super().__init__()
        self.dependencies = dependencies

    def run(self):
        pass


class DepsCollwOuts(Node):
    dependencies = dvc.deps()
    outs: Path = dvc.outs()

    def __init__(self, dependencies):
        super().__init__()
        self.outs = Path("lorem.txt")
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

    DVCOuts().write_dvc()

    DependenciesCollector(dependencies=DVCOuts.load()).write_dvc()

    subprocess.check_call(["dvc", "repro"])

    assert (
        DependenciesCollector.load().dependencies.data_file.read_text() == "Lorem Ipsum"
    )


def test_zn_outs(dvc_repo_path):
    os.chdir(dvc_repo_path)

    ZnOuts().write_dvc()

    DependenciesCollector(dependencies=ZnOuts.load()).write_dvc()

    subprocess.check_call(["dvc", "repro"])

    assert DependenciesCollector.load().dependencies.data == "Lorem Ipsum"


def test_dvc_zn_outs(dvc_repo_path):
    os.chdir(dvc_repo_path)

    DVCZnOuts().write_dvc()

    DependenciesCollector(dependencies=DVCZnOuts.load()).write_dvc()

    subprocess.check_call(["dvc", "repro"])

    assert (
        DependenciesCollector.load().dependencies.data_file.read_text() == "Lorem Ipsum"
    )

    assert DependenciesCollector.load().dependencies.data == "Lorem Ipsum"


# def test_expand_dependencies(dvc_repo_path):
#     os.chdir(dvc_repo_path)
#
#     DVCZnOuts().write_dvc()
#
#     dependencies_collector = DependenciesCollector(name="Collector01")
#     dependencies_collector(dependencies=DVCZnOuts(load=True))
#
#     dependencies_collector = DependenciesCollector(name="Collector02")
#     dependencies_collector(
#         dependencies=DependenciesCollector(name="Collector01", load=True)
#     )
#
#     subprocess.check_call(["dvc", "repro"])


# def _test_exp_deps_w_outs(dvc_repo_path):
#     """test_expand_dependencies_with_outs"""
#     os.chdir(dvc_repo_path)
#
#     dvc_zn_outs = DVCZnOuts()
#     dvc_zn_outs()
#
#     dependencies_collector = DepsCollwOuts(name="Collector01")
#     dependencies_collector(dependencies=DVCZnOuts(load=True))
#
#     dependencies_collector = DepsCollwOuts(name="Collector02")
#     dependencies_collector(dependencies=DepsCollwOuts(name="Collector01", load=True))
#
#     subprocess.check_call(["dvc", "repro"])
