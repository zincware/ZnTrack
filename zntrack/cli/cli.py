"""The ZnTrack CLI."""

import contextlib
import datetime
import importlib.metadata
import os
import pathlib
import sys

import git
import typer
import yaml

from zntrack import Node, config, utils
from zntrack.state import PLUGIN_LIST
from zntrack.utils.import_handler import import_handler
from zntrack.utils.list_nodes import list_nodes
from zntrack.utils.lockfile import mp_join_stage_lock, mp_start_stage_lock
from zntrack.utils.misc import load_env_vars

load_env_vars()

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


def parse_command_from_dvc_yaml(stage_name: str) -> tuple[str, str | None]:
    """Parse the command from dvc.yaml for a given stage name.

    Arguments:
    ---------
    stage_name : str
        The name of the stage in dvc.yaml

    Returns:
    -------
    tuple[str, str | None]
        A tuple of (node_path, name) extracted from the command

    Raises:
    ------
    FileNotFoundError
        If dvc.yaml is not found
    ValueError
        If the stage is not found in dvc.yaml or command cannot be parsed

    """
    dvc_yaml_path = config.DVC_FILE_PATH
    if not dvc_yaml_path.exists():
        raise FileNotFoundError(
            f"{config.DVC_FILE_PATH} not found. Make sure you're in the project root directory."
        )

    with dvc_yaml_path.open() as f:
        dvc_config = yaml.safe_load(f)

    if "stages" not in dvc_config:
        raise ValueError(f"No stages found in {config.DVC_FILE_PATH}")

    if stage_name not in dvc_config["stages"]:
        available_stages = ", ".join(dvc_config["stages"].keys())
        raise ValueError(
            f"Stage '{stage_name}' not found in {config.DVC_FILE_PATH}. "
            f"Available stages: {available_stages}"
        )

    stage = dvc_config["stages"][stage_name]
    if "cmd" not in stage:
        raise ValueError(
            f"No command found for stage '{stage_name}' in {config.DVC_FILE_PATH}"
        )

    cmd = stage["cmd"]

    # Parse the command: "zntrack run module.Node --name node_name"
    # Split by whitespace and parse arguments
    parts = cmd.split()

    if len(parts) < 3 or parts[0] != "zntrack" or parts[1] != "run":
        raise ValueError(
            f"Unexpected command format in {config.DVC_FILE_PATH} for stage '{stage_name}': {cmd}"
        )

    node_path = parts[2]
    name = None

    # Look for --name argument
    if "--name" in parts:
        name_idx = parts.index("--name")
        if name_idx + 1 < len(parts):
            name = parts[name_idx + 1]

    return node_path, name


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
    node_path: str,
    name: str = None,
    meta_only: bool = False,
    method: str = "run",
    save_lockfile: bool = True,
) -> None:
    """Execute a ZnTrack Node.

    Use as 'zntrack run module.Node --name node_name' or 'zntrack run <node-name>'.

    When providing just a node name (without dots), the command will be parsed from dvc.yaml.

    Arguments:
    ---------
    node_path : str
        The full path to the Node (e.g. `ipsuite.nodes.SmilesToAtoms`) or
        the name of a stage in dvc.yaml (e.g. `MyNode`)
    name : str
        The name of the node. If not provided and node_path is a stage name,
        it will be extracted from dvc.yaml.
    meta_only : bool
        Save only the metadata.
    method : str, default 'run'
        The method to run on the node.
    save_lockfile : bool
        Save the lockfile for the inputs into the node-meta.json file.

    """
    start_time = datetime.datetime.now()

    # If node_path doesn't contain a dot, treat it as a stage name from dvc.yaml
    if "." not in node_path:
        try:
            parsed_node_path, parsed_name = parse_command_from_dvc_yaml(node_path)
            # Use parsed values if not overridden by command line arguments
            if name is None:
                name = parsed_name
            node_path = parsed_node_path
        except (FileNotFoundError, ValueError) as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from e

    utils.misc.load_env_vars(name)
    sys.path.append(pathlib.Path.cwd().as_posix())

    cls: Node = utils.import_handler.import_handler(node_path)
    node: Node = cls.from_rev(name=name, running=True)
    if save_lockfile:
        queue, proc = mp_start_stage_lock(name)
    node.state.increment_run_count()
    node.state.save_node_meta()
    # dynamic version of node.run()
    getattr(node, method)()
    node.save()
    if save_lockfile:
        stage_lock = mp_join_stage_lock(queue, proc)
        node.state.set_lockfile(stage_lock)
    run_time = datetime.datetime.now() - start_time
    node.state.add_run_time(run_time)

    node.state.save_node_meta()


@app.command()
def list(
    remote: str = typer.Argument(None, help="The path/url to the repository"),
    rev: str = typer.Argument(None, help="The revision to list (default: HEAD)"),
    json: bool = typer.Option(False, help="Output in JSON format."),
):
    """List all Nodes in the Project."""
    df = list_nodes(remote=remote, rev=rev, verbose=0 if json else 1)
    if json:
        typer.echo(df.to_json(orient="records", indent=2))


@app.command()
def finalize(
    skip_cached: bool = typer.Option(True, help="Do not upload cached nodes."),
    update_run_names: bool = typer.Option(
        True, help="Include part of the commit message in the run names."
    ),
):
    """Post-commit step for plugin integration."""
    utils.misc.load_env_vars()
    plugins_paths = os.environ.get(
        "ZNTRACK_PLUGINS", "zntrack.plugins.dvc_plugin.DVCPlugin"
    )
    plugins: PLUGIN_LIST = [import_handler(p) for p in plugins_paths.split(",")]
    for plugin in plugins:
        plugin.finalize(skip_cached=skip_cached, update_run_names=update_run_names)
