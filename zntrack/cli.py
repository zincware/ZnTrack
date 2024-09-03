"""The ZnTrack CLI."""

import contextlib
import importlib.metadata
import pathlib
import sys

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
def run(
    node_path: str, name: str = None, meta_only: bool = False, method: str = "run"
) -> None:
    """Execute a ZnTrack Node.

    Use as 'zntrack run module.Node --name node_name'.

    Arguments:
    ---------
    node_path : str
        The full path to the Node, e.g. `ipsuite.nodes.SmilesToAtoms`
    name : str
        The name of the node.
    meta_only : bool
        Save only the metadata.
    method : str, default 'run'
        The method to run on the node.

    """
    utils.misc.load_env_vars(name)
    sys.path.append(pathlib.Path.cwd().as_posix())

    cls: Node = utils.import_handler.import_handler(node_path)
    node: Node = cls.from_rev(name=name, running=True)
    node.update_run_count()
    node.run()
    node.save()

    # if getattr(cls, "is_node", False):
    #     cls(exec_func=True)
    # elif issubclass(cls, Node):
    #     node: Node = cls.from_rev(name=name, results=False)
    #     node.save(meta_only=True)
    #     if not meta_only:
    #         # dynamic version of node.run()
    #         getattr(node, method)()
    #         node.save(parameter=False)
    # else:
    #     raise ValueError(f"Node {node} is not a ZnTrack Node.")


@app.command()
def list(
    remote: str = typer.Argument(".", help="The path/url to the repository"),
    rev: str = typer.Argument(None, help="The revision to list (default: HEAD)"),
):
    """List all Nodes in the Project."""
    groups, _ = utils.cli.get_groups(remote, rev)
    print(yaml.dump(groups))