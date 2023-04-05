"""The ZnTrack CLI."""
import contextlib
import importlib.metadata
import os
import pathlib
import sys
import uuid

import git
import typer
import yaml

from zntrack import Node, utils

app = typer.Typer()


def version_callback(value: bool) -> None:
    """Get the installed 'ZnTrack' version."""
    if value:
        path = pathlib.Path(__file__).parent.parent.parent
        report = f"ZnTrack {importlib.metadata.version('zntrack')} at '{path}'"

        with contextlib.suppress(git.exc.InvalidGitRepositoryError):
            repo = git.Repo(path)
            _ = repo.git_dir

            report += " - "
            with contextlib.suppress(TypeError):  # detached head
                report += f"{repo.active_branch.name}@"
            report += f"{repo.head.object.hexsha[:7]}"
            if repo.is_dirty():
                report += " (dirty)"

        typer.echo(report)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
) -> None:
    """ZnTrack CLI main callback."""
    _ = version  # this would be greyed out otherwise


@app.command()
def run(node: str, name: str = None, hash_only: bool = False) -> None:
    """Execute a ZnTrack Node.

    Use as 'zntrack run module.Node --name node_name'.
    """
    env_file = pathlib.Path("env.yaml")
    if env_file.exists():
        env = yaml.safe_load(env_file.read_text())
        for key, value in env.get(name, {}).items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    sys.path.append(pathlib.Path.cwd().as_posix())

    package_and_module, cls = node.rsplit(".", 1)
    module = importlib.import_module(package_and_module)

    cls = getattr(module, cls)

    if getattr(cls, "is_node", False):
        cls(exec_func=True)
    elif issubclass(cls, Node):
        node: Node = cls.from_rev(name=name, results=False)
        if hash_only:
            (node.nwd / "hash").write_text(str(uuid.uuid4()))
        else:
            node.run()
            node.save(parameter=False)
    else:
        raise ValueError(f"Node {node} is not a ZnTrack Node.")


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
    """Initialize a new ZnTrack Project."""
    initializer = utils.cli.Initializer(name=name, gitignore=gitignore, force=force)
    initializer.run()
