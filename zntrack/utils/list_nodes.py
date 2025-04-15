import json

import dvc.api
import pandas as pd
import znjson
from rich.console import Console
from rich.text import Text
from rich.tree import Tree

import zntrack


# Extract node data into a DataFrame
def extract_node_info(node):
    group = node.state.group.names if node.state.group is not None else None
    full_name = node.state.name
    if group:
        group_prefix = "_".join(group) + "_"
        if full_name.startswith(group_prefix):
            short_name = full_name[len(group_prefix) :]
        else:
            short_name = full_name  # fallback
    else:
        short_name = full_name

    return {
        "name": short_name,
        "full_name": full_name,
        "group": group,
        "changed": node.state.changed,
    }


# Build a forest of nested group trees
def build_forest(df: pd.DataFrame) -> list:
    forest = []
    grouped = df.groupby(df["group"].apply(lambda g: g or ("__NO_GROUP__",)))
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


# Format rich tree nodes
def format_node(short_name: str, full_name: str, changed: bool) -> Text:
    status = "✅" if not changed else "❌"
    text = Text(f"{short_name} {status}")
    if short_name != full_name:
        text.append(f" -> {full_name}", style="dim")
    return text


def list_nodes(remote: str | None = None, rev: str | None = None) -> pd.DataFrame:
    # Load DVC-tracked zntrack.json
    fs = dvc.api.DVCFileSystem(url=remote, rev=rev)
    with fs.open("zntrack.json", "r") as f:
        config = json.load(f, cls=znjson.ZnDecoder)

    # Load all nodes from DVC revision
    nodes = [zntrack.from_rev(name=name) for name in config]
    df = pd.DataFrame([extract_node_info(node) for node in nodes])

    # Render the trees
    console = Console()
    for top_tree in build_forest(df):
        console.print(top_tree)

    return df
