import json
from pathlib import Path, PurePosixPath

import dvc.api
import pandas as pd
from rich.console import Console
from rich.text import Text
from rich.tree import Tree
from zntrack.group import Group
import zntrack

from dvc.stage import Stage, PipelineStage


def normalize_path(path: str) -> PurePosixPath:
    """Clean up path, removing '..' and '.'."""
    parts = [p for p in PurePosixPath(path).parts if p not in ("..", ".")]
    return PurePosixPath(*parts)


def format_node(short_name: str, full_name: str, changed: bool) -> Text:
    """Format tree leaf node."""
    status = "✅" if not changed else "❌"
    text = Text(f"{short_name} {status}")
    if short_name != full_name:
        text.append(f" -> {full_name}", style="dim")
    return text


def build_forest(df: pd.DataFrame) -> list[Tree]:
    """Build nested tree from dataframe grouped by 'group' column."""
    forest = []
    grouped = df.groupby(df["group"])
    trees_by_path = {}

    for group_path, items in grouped:
        group_path = tuple(group_path)

        for i, part in enumerate(group_path):
            path = group_path[: i + 1]
            if path not in trees_by_path:
                node_name = "📁 No Group" if part == "__NO_GROUP__" else f"📁 {part}"
                tree = Tree(node_name)
                trees_by_path[path] = tree
                if i == 0:
                    forest.append(tree)
                else:
                    trees_by_path[group_path[:i]].add(tree)

        for _, row in items.iterrows():
            trees_by_path[group_path].add(
                format_node(row["name"], row["full_name"], row["changed"])
            )

    return forest


def list_nodes(remote: str | None = None, rev: str | None = None, verbose: int = 1) -> pd.DataFrame:
    """List zntrack nodes from DVC repo and display a nested tree."""
    fs = dvc.api.DVCFileSystem(url=remote, rev=rev)
    stages: list[Stage | PipelineStage] = list(fs.repo.stage.collect())
    node_data = []

    for stage in stages:
        if not isinstance(stage, PipelineStage):
            continue

        # Determine stage_name and dvc_path if possible
        if ":" in stage.addressing:
            dvc_path_str, stage_name = stage.addressing.split(":")
            # Exclude 'dvc.yaml' from the dvc_parts for grouping
            dvc_path_obj = normalize_path(dvc_path_str)
            dvc_parts = tuple(p for p in dvc_path_obj.parts if p != "dvc.yaml")
        else:
            # Single file project
            stage_name = stage.addressing
            # If addressing is a dvc.yaml, we treat its parent as the dvc_parts
            if stage_name == "dvc.yaml":
                dvc_parts = () # no dvc_parts if it's just dvc.yaml in root
            elif PurePosixPath(stage_name).name == "dvc.yaml":
                dvc_parts = PurePosixPath(stage_name).parent.parts
            else:
                dvc_parts = ()

        short_name = stage.name

        # Load zntrack group per node (from its nwd)
        try:
            config_path = Path(stage.path_in_repo).parent / "zntrack.json"
            config = json.loads(fs.read_text(config_path))
            nwd = config[stage.name]["nwd"]["value"]
            group = Group.from_nwd(Path(nwd))
            group_parts = tuple(group.names) if group.names else ()
        except Exception as e:
            group_parts = ()

        # Build group path
        if dvc_parts and group_parts:
            group_path = dvc_parts + group_parts
        elif dvc_parts:
            group_path = dvc_parts
        elif group_parts:
            group_path = group_parts
        else:
            group_path = ("__NO_GROUP__",)

        node_data.append({
            "name": short_name,
            "full_name": stage.addressing,
            "group": group_path,
            "changed": False
        })

    df = pd.DataFrame(node_data)

    # Render tree
    if verbose > 0:
        console = Console()
        for top_tree in build_forest(df):
            console.print(top_tree)

    return df