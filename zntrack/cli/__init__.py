import importlib.metadata
import pathlib
import sys

import typer

app = typer.Typer()


def version_callback(value: bool) -> None:
    """Get the installed 'ZnTrack' version."""
    if value:
        typer.echo(f"ZnTrack {importlib.metadata.version('zntrack')}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
) -> None:
    """The ZnTrack CLI."""
    _ = version  # this would be greyed out otherwise


@app.command()
def run(node: str, name: str = None, hash_only: bool = False) -> None:
    """Execute a ZnTrack Node.

    Use as 'zntrack run module.Node --name node_name'.
    """
    sys.path.append(pathlib.Path.cwd().as_posix())

    package_and_module, cls = node.rsplit(".", 1)
    module = importlib.import_module(package_and_module)

    cls = getattr(module, cls)

    try:
        node = cls.load(name=name)
        if hash_only:
            node.save(hash_only=True)
        else:
            node.run_and_save()
    except AttributeError:
        # @nodify function
        cls(exec_func=True)
