import typer

from zntrack import __version__

app = typer.Typer()


@app.command()
def init(name: str = "MyProject"):
    """
    <update me>
    """
    typer.echo(f"Creating new project: {name}")


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
