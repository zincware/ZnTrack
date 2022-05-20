import dataclasses
import pathlib
import subprocess
import urllib.request

import typer

from zntrack import __version__

app = typer.Typer()


@dataclasses.dataclass
class Initializer:
    name: str
    gitignore: bool
    force: bool
    src: pathlib.Path = pathlib.Path("src")

    _gitignore_url: str = (
        "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore"
    )

    def run(self):
        self.check_empty()
        typer.echo(f"Creating new project: {self.name}")
        self.make_src()
        self.make_repo()
        self.write_main_file()
        self.write_readme()
        if self.gitignore:
            self.write_gitignore()

    def check_empty(self):
        """Check if the project directory is empty

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
        self.src.mkdir()
        (self.src / "__init__.py").touch()

    def write_gitignore(self):
        gitignore = pathlib.Path(".gitignore")
        with urllib.request.urlopen(self._gitignore_url) as url:
            gitignore.write_text(url.read().decode("utf-8"))

    def write_main_file(self):
        pathlib.Path("main.py").touch()

    def write_readme(self):
        pathlib.Path("README.md").write_text(f"# Welcome to {self.name}")

    def make_repo(self):
        subprocess.check_call(["git", "init"])
        subprocess.check_call(["dvc", "init"])


@app.command()
def init(
    name: str = "New Project",
    gitignore: bool = typer.Option(
        False, help="Create a gitignore file with all the usual files excluded."
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Initialize Project if the directory is not empty."
    ),
):
    """
    <update me>
    """
    initializer = Initializer(name=name, gitignore=gitignore, force=force)
    initializer.run()


def version_callback(value: bool):
    """Get the installed zntrack version"""
    if value:
        typer.echo(f"ZnTrack {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    """
    <update me>
    """
    _ = version  # this would be greyed out otherwise
