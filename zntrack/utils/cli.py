"""CLI Helpers."""
import dataclasses
import pathlib
import subprocess
import urllib.request

import typer


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
