import importlib.metadata
import pathlib
import sys

import typer

app = typer.Typer()


def version_callback(value: bool) -> None:
    """Get the installed dask4dvc version."""
    if value:
        typer.echo(f"ZnTrack {importlib.metadata.version('zntrack')}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
) -> None:
    """ZnTrack CLI callback."""
    _ = version  # this would be greyed out otherwise


@app.command()
def run(cmd: str) -> None:
    """Execute a ZnTrack Node.

    Use as `zntrack run module.Node^name=nodename` or in `zntrack run module.nodified`.
    """
    sys.path.append(pathlib.Path.cwd().as_posix())

    cmd, *kwargs = cmd.split("^")
    kwargs = [tuple(arg.split("=")) for arg in kwargs]
    package_and_module, cls = cmd.split(".", 1)
    module = importlib.import_module(package_and_module)

    cls = getattr(module, cls)

    try:
        node = cls.load(**dict(kwargs))
        node.run_and_save()
    except AttributeError:
        cls(exec_func=True, **dict(kwargs))
