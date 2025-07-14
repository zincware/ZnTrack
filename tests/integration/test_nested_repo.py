import os
import pathlib

import pytest
from dvc.api import DVCFileSystem
from git import Repo

import zntrack.examples


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

    # now try loading the node using an absolute path
    with pytest.raises(FileNotFoundError):
        # DVCFileSystem struggles with absolute paths
        node_loaded = zntrack.from_rev(
            "subrepo/dvc.yaml:ParamsToOuts",
            remote=proj_path.resolve().as_posix(),
        )


def test_subrepo_external_node(proj_path):
    """Test subrepo functionality with external dataclasses."""
    # Create external node module file that can be imported
    external_module_content = """
from dataclasses import dataclass

@dataclass
class ExampleExternalNode:
    parameter: str
"""

    external_module_path = proj_path / "external_nodes.py"
    with open(external_module_path, "w") as f:
        f.write(external_module_content)

    # Import the external node from the file
    import importlib.util
    import sys

    # Store original sys.modules state for cleanup
    original_modules = sys.modules.copy()

    try:
        spec = importlib.util.spec_from_file_location(
            "external_nodes", external_module_path
        )
        external_nodes = importlib.util.module_from_spec(spec)
        sys.modules["external_nodes"] = external_nodes
        spec.loader.exec_module(external_nodes)

        example_external_node = external_nodes.ExampleExternalNode

        directory = pathlib.Path("subrepo")
        directory.mkdir(parents=True, exist_ok=True)
        os.chdir(directory)

        project = zntrack.Project()

        ext_node = example_external_node(parameter="Lorem Ipsum")

        with project:
            node = zntrack.examples.OptionalDeps(
                value=ext_node,
            )
        project.build()

        os.chdir(proj_path)

        assert node.value.parameter == "Lorem Ipsum"

        # Test: External dependencies behavior with nested repos
        # Remove the module from sys.modules to simulate it not being available
        if "external_nodes" in sys.modules:
            del sys.modules["external_nodes"]

        # Load node - should raise error when external module is not available
        node = zntrack.from_rev("subrepo/dvc.yaml:OptionalDeps")
        # The value itself will be NOT_AVAILABLE, but accessing attributes should raise
        assert node.value is zntrack.NOT_AVAILABLE

        # Accessing attributes on NOT_AVAILABLE should raise helpful error
        with pytest.raises(
            ModuleNotFoundError, match="Cannot access attribute.*external dependency"
        ):
            _ = node.value.parameter

    finally:
        # Restore original sys.modules state to avoid affecting other tests
        sys.modules.clear()
        sys.modules.update(original_modules)
