import os
import pathlib
from dataclasses import dataclass

from dvc.api import DVCFileSystem
from git import Repo

import zntrack.examples


@dataclass
class ExampleExternalNode:
    parameter: str


def test_subrepo(proj_path):
    """Test subrepo functionality"""
    directory = pathlib.Path("subrepo")
    directory.mkdir(parents=True, exist_ok=True)
    os.chdir(directory)

    project = zntrack.Project()
    with project:
        node = zntrack.examples.ParamsToOuts(
            params={"param1": 1, "param2": 2},
        )
    project.repro()

    os.chdir(proj_path)

    node_loaded = zntrack.from_rev(
        "subrepo/dvc.yaml:ParamsToOuts",
    )
    assert node_loaded.params == {"param1": 1, "param2": 2}
    assert node_loaded.outs == {"param1": 1, "param2": 2}

    # now test with DVCFs
    node_loaded = zntrack.from_rev("subrepo/dvc.yaml:ParamsToOuts", fs=DVCFileSystem())
    assert node_loaded.params == {"param1": 1, "param2": 2}
    assert node_loaded.outs == {"param1": 1, "param2": 2}

    # make a commit and change things

    repo = Repo()
    repo.git.add(all=True)
    repo.index.commit("Initial commit")

    os.chdir(directory)
    node.params = {"param1": 3, "param2": 4}
    project.repro()
    os.chdir(proj_path)

    node_loaded = zntrack.from_rev(
        "subrepo/dvc.yaml:ParamsToOuts",
    )
    assert node_loaded.params == {"param1": 3, "param2": 4}
    assert node_loaded.outs == {"param1": 3, "param2": 4}

    node_loaded = zntrack.from_rev("subrepo/dvc.yaml:ParamsToOuts", rev="HEAD")
    assert node_loaded.params == {"param1": 1, "param2": 2}
    assert node_loaded.outs == {"param1": 1, "param2": 2}


def test_subrepo_external_node(proj_path):
    """Test subrepo functionality"""
    directory = pathlib.Path("subrepo")
    directory.mkdir(parents=True, exist_ok=True)
    os.chdir(directory)

    project = zntrack.Project()

    ext_node = ExampleExternalNode(parameter="Lorem Ipsum")

    with project:
        node = zntrack.examples.OptionalDeps(
            value=ext_node,
        )
    project.build()

    os.chdir(proj_path)

    node = zntrack.from_rev(
        "subrepo/dvc.yaml:OptionalDeps",
    )
    assert node.value.parameter == "Lorem Ipsum"

    # now test with DVCFs
    node = zntrack.from_rev("subrepo/dvc.yaml:OptionalDeps", fs=DVCFileSystem())
    assert node.value.parameter == "Lorem Ipsum"

    # make a commit and change things
    repo = Repo()
    repo.git.add(all=True)
    repo.index.commit("Initial commit")
    os.chdir(directory)
    ext_node.parameter = "Dolor Sit Amet"
    project.build()
    os.chdir(proj_path)
    node = zntrack.from_rev(
        "subrepo/dvc.yaml:OptionalDeps",
    )

    assert node.value.parameter == "Dolor Sit Amet"

    node = zntrack.from_rev("subrepo/dvc.yaml:OptionalDeps", rev="HEAD")
    assert node.value.parameter == "Lorem Ipsum"
