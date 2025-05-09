import json
import pathlib
from typing import Tuple

from dvc.api import DVCFileSystem

from zntrack.config import ZNTRACK_FILE_PATH


def get_groups(remote, rev) -> Tuple[dict, list]:
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
        A nested dictionary with the group names as keys and the nodes in each group as
        values. Contains "short-name -> long-name" if inside a group.
    node_names: list
        A list of all node names in the project.

    """
    fs = DVCFileSystem(url=remote, rev=rev)
    with fs.open(ZNTRACK_FILE_PATH) as f:
        config = json.load(f)

    true_groups = {}
    node_names = []

    def add_to_group(groups, grp_names, node_name):
        """Recursively add node_name into the correct nested group structure."""
        if not grp_names:
            return

        current_group = grp_names[0]

        # If this is the last level, add the node directly
        if len(grp_names) == 1:
            if current_group not in groups:
                groups[current_group] = []
            groups[current_group].append(node_name)
        else:
            # Ensure the current group contains a dictionary inside a list
            if current_group not in groups:
                groups[current_group] = [{}]
            elif not isinstance(groups[current_group][0], dict):
                groups[current_group].insert(0, {})

            add_to_group(groups[current_group][0], grp_names[1:], node_name)

    for node_name, node_config in config.items():
        nwd = pathlib.Path(node_config["nwd"]["value"])
        grp_names = nwd.parent.as_posix().split("/")[1:]

        if not grp_names:
            node_names.append(node_name)
            grp_names = ["nodes"]
        else:
            for grp_name in grp_names:
                node_name = node_name.replace(f"{grp_name}_", "")

            node_names.append(f"{'_'.join(grp_names)}_{node_name}")
            node_name = f"{node_name} -> {node_names[-1]}"

        add_to_group(true_groups, grp_names, node_name)

    return true_groups, node_names
