"""CLI Helpers."""

import dataclasses
import json
import pathlib
import subprocess
import urllib.request

import typer
from dvc.api import DVCFileSystem


@dataclasses.dataclass
class Initializer:
    """Initialize a new ZnTrack Project."""

    name: str
    gitignore: bool
    force: bool
    src: pathlib.Path = pathlib.Path("src")

    _gitignore_url: str = (
        "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore"
    )

    def run(self):
        """Run the initializer."""
        self.check_empty()
        typer.echo(f"Creating new project: {self.name}")
        self.make_src()
        self.make_repo()
        self.write_main_file()
        self.write_readme()
        if self.gitignore:
            self.write_gitignore()

    def check_empty(self):
        """Check if the project directory is empty.

        Raises
        ------
        typer.Exit: if the directory is not empty and force is false
        """
        is_empty = not any(pathlib.Path(".").iterdir())
        if not is_empty and not self.force:
            typer.echo(
                "The current working directory is not empty. If you want to initialize a"
                " project anyway use 'zntrack init --force'."
            )
            raise typer.Exit()

    def make_src(self):
        """Create a src directory that contains the Node configurations."""
        self.src.mkdir()
        init_file = self.src / "__init__.py"
        init_file.write_text(r'"""ZnTrack Node module."""')

    def write_gitignore(self):
        """Create a gitignore file based on the Python gitignore template."""
        gitignore = pathlib.Path(".gitignore")
        with urllib.request.urlopen(self._gitignore_url) as url:
            gitignore.write_text(url.read().decode("utf-8"))

    def write_main_file(self):
        """Create a 'main.py' file."""
        pathlib.Path("main.py").touch()

    def write_readme(self):
        """Create a README.md file."""
        pathlib.Path("README.md").write_text(f"# Welcome to {self.name} \n")

    def make_repo(self):
        """Initialize the repository."""
        subprocess.check_call(["git", "init"])
        subprocess.check_call(["dvc", "init"])


def get_groups(remote, rev) -> (dict, list):
    """Get the group names and the nodes in each group from the remote.

    Arguments:
    ---------
    remote : str
        The remote to get the group names from.
    rev : str
        The revision to use.

    Returns:
    -------
    groups : dict
        a nested dictionary with the group names as keys and the nodes in each group as
        values. Contains "short-name -> long-name" if inside a group.
    node_names: list
        A list of all node names in the project.
    """
    fs = DVCFileSystem(url=remote, rev=rev)
    with fs.open("zntrack.json") as f:
        config = json.load(f)

    true_groups = {}
    node_names = []

    def add_to_group(groups, grp_names, node_name):
        if len(grp_names) == 1:
            if grp_names[0] not in groups:
                groups[grp_names[0]] = []
            groups[grp_names[0]].append(node_name)
        else:
            if grp_names[0] not in groups:
                groups[grp_names[0]] = [{}]
            add_to_group(groups[grp_names[0]][0], grp_names[1:], node_name)

    for node_name, node_config in config.items():
        nwd = pathlib.Path(node_config["nwd"]["value"])
        grp_names = nwd.parent.as_posix().split("/")[1:]
        if len(grp_names) == 0:
            node_names.append(node_name)
            grp_names = ["nodes"]
        else:
            for grp_name in grp_names:
                node_name = node_name.replace(f"{grp_name}_", "")

            node_names.append(f"{'_'.join(grp_names)}_{node_name}")
            node_name = f"{node_name} -> {node_names[-1]}"
        add_to_group(true_groups, grp_names, node_name)

    return true_groups, node_names
