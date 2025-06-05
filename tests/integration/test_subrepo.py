import os
import pathlib
from dataclasses import dataclass

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

    node = zntrack.from_rev(
        "subrepo/dvc.yaml:ParamsToOuts",
    )
    assert node.params == {"param1": 1, "param2": 2}
    assert node.outs == {"param1": 1, "param2": 2}


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
    # node = zntrack.from_rev("OptionalDeps")
    assert node.value.parameter == "Lorem Ipsum"
