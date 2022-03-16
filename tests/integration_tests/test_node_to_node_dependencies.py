import os
import shutil
import subprocess
from pathlib import Path

import pytest

from zntrack import dvc, getdeps, zn
from zntrack.core.base import Node


class DVCOuts(Node):
    data_file: Path = dvc.outs()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file = Path("data")

    def run(self):
        self.data_file.write_text("Lorem Ipsum")


class ZnOuts(Node):
    data: str = zn.outs()

    def run(self):
        self.data = "Lorem Ipsum"

    @property
    def reverse(self):
        return self.data[::-1]


class DVCZnOuts(Node):
    data_file: Path = dvc.outs()
    data: str = zn.outs()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file = Path("data")

    def run(self):
        self.data_file.write_text("Lorem Ipsum")
        self.data = "Lorem Ipsum"


class DependenciesCollector(Node):
    dependencies = dvc.deps()

    def __init__(self, dependencies=None, **kwargs):
        super().__init__(**kwargs)
        self.dependencies = dependencies

    def run(self):
        pass


class DepsCollwOuts(Node):
    dependencies = dvc.deps()
    outs: Path = dvc.outs()

    def __init__(self, dependencies=None, **kwargs):
        super().__init__(**kwargs)
        # must add a name, if the Node is used with two different names to avoid
        # writing to the same file!
        self.outs = Path(f"{self.node_name}_lorem.txt")
        self.dependencies = dependencies

    def run(self):
        self.outs.write_text("Lorem Ipsum")


@pytest.fixture()
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


def test_dvc_outs(proj_path):
    DVCOuts().write_graph()

    DependenciesCollector(dependencies=DVCOuts.load()).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert (
        DependenciesCollector.load().dependencies.data_file.read_text() == "Lorem Ipsum"
    )


def test_dvc_outs_no_load(proj_path):
    DVCOuts().write_graph()
    assert issubclass(DVCOuts, Node)
    DependenciesCollector(dependencies=DVCOuts).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert (
        DependenciesCollector.load().dependencies.data_file.read_text() == "Lorem Ipsum"
    )


def test_dvc_reversed(proj_path):
    """Create the instances first and at the end call write_graph"""
    with pytest.raises(AttributeError):
        # this can not work, because DVCOuts affected files is not now at the stage
        # where DependenciesCollector writes its DVC stage
        DependenciesCollector(dependencies=DVCOuts.load()).write_graph()
        DVCOuts().write_graph()


def test_zn_outs(proj_path):
    ZnOuts().write_graph()

    DependenciesCollector(dependencies=ZnOuts.load()).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert DependenciesCollector.load().dependencies.data == "Lorem Ipsum"


def test_dvc_zn_outs(proj_path):
    DVCZnOuts().write_graph()

    DependenciesCollector(dependencies=DVCZnOuts.load()).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert (
        DependenciesCollector.load().dependencies.data_file.read_text() == "Lorem Ipsum"
    )

    assert DependenciesCollector.load().dependencies.data == "Lorem Ipsum"


def test_expand_dependencies(proj_path):
    DVCZnOuts().write_graph()

    DependenciesCollector(name="Collector01", dependencies=DVCZnOuts.load()).write_graph()
    DependenciesCollector(name="Collector02", dependencies=DVCZnOuts.load()).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert (
        DependenciesCollector.load(name="Collector01").dependencies.data == "Lorem Ipsum"
    )
    assert (
        DependenciesCollector.load(name="Collector02").dependencies.data == "Lorem Ipsum"
    )


def test_exp_deps_w_outs(proj_path):
    """test_expand_dependencies_with_outs"""
    DVCZnOuts().write_graph()

    DepsCollwOuts(name="Collector01", dependencies=DVCZnOuts.load()).write_graph()
    DepsCollwOuts(
        name="Collector02", dependencies=DepsCollwOuts.load(name="Collector01")
    ).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert DepsCollwOuts.load("Collector01").dependencies.data == "Lorem Ipsum"
    assert (
        DepsCollwOuts.load("Collector02").dependencies.dependencies.data == "Lorem Ipsum"
    )


def test_multiple_deps(proj_path):
    DVCOuts().save()
    ZnOuts().save()

    DependenciesCollector(dependencies=[DVCOuts.load(), ZnOuts.load()]).save()

    assert DVCOuts.load().data_file == Path("data")

    deps_col = DependenciesCollector.load()

    assert isinstance(deps_col.dependencies[0], DVCOuts)
    assert isinstance(deps_col.dependencies[1], ZnOuts)

    assert deps_col.dependencies[0].data_file == Path("data")

    # from DVCOuts
    assert "data" in deps_col.write_graph(dry_run=True)
    # from ZnOuts
    assert "nodes/ZnOuts/outs.json" in deps_col.write_graph(dry_run=True)


class DefaultDependencyNode(Node):
    deps: ZnOuts = zn.deps(ZnOuts.load())
    result = zn.outs()

    def run(self):
        self.result = self.deps.data


def test_default_dependency(proj_path):
    """Test that an instance of a dependency is loaded correctly when a new
    instance is created"""
    ZnOuts().write_graph()
    subprocess.check_call(["dvc", "repro"])
    DefaultDependencyNode().run_and_save()

    assert DefaultDependencyNode.load().result == "Lorem Ipsum"


@pytest.mark.parametrize("load", (True, False))
def test_getdeps(proj_path, load):
    DVCOuts().write_graph()

    if load:
        deps = getdeps(DVCOuts.load(), "data_file")
    else:
        deps = getdeps(DVCOuts, "data_file")

    DependenciesCollector(dependencies=deps).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert DependenciesCollector.load().dependencies.read_text() == "Lorem Ipsum"


def test_getdeps_named(proj_path):
    DVCOuts(name="node01").write_graph()

    DependenciesCollector(
        dependencies=getdeps(DVCOuts.load("node01"), "data_file")
    ).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert DependenciesCollector.load().dependencies.read_text() == "Lorem Ipsum"


def test_getdeps_named_multi(proj_path):
    DVCOuts(name="node01").write_graph()
    ZnOuts(name="node02").write_graph()

    DependenciesCollector(
        dependencies=[
            getdeps(DVCOuts.load("node01"), "data_file"),
            getdeps(ZnOuts.load("node02"), "data"),
        ]
    ).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert DependenciesCollector.load().dependencies[0].read_text() == "Lorem Ipsum"
    assert DependenciesCollector.load().dependencies[1] == "Lorem Ipsum"


@pytest.mark.parametrize("load", (True, False))
def test_getdeps_property(proj_path, load):
    ZnOuts().write_graph()
    if load:
        deps = getdeps(ZnOuts.load(), "reverse")
    else:
        deps = getdeps(ZnOuts, "reverse")

    DependenciesCollector(dependencies=deps).write_graph()

    subprocess.check_call(["dvc", "repro"])

    assert DependenciesCollector.load().dependencies == "muspI meroL"
