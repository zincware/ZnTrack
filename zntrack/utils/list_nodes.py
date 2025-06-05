import json
from pathlib import Path

import dvc.api
import pandas as pd
from rich.console import Console
from rich.text import Text
from rich.tree import Tree
from zntrack.group import Group
import zntrack

from dvc.stage import Stage, PipelineStage


# --- Tree Building and Formatting ---

def build_forest(df: pd.DataFrame) -> list[Tree]:
    """Build a forest of nested group trees from a DataFrame."""
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


def format_node(short_name: str, full_name: str, changed: bool) -> Text:
    """Format a single tree node with change status."""
    status = "✅" if not changed else "❌"
    text = Text(f"{short_name} {status}")
    if short_name != full_name:
        text.append(f" -> {full_name}", style="dim")
    return text


# --- Node Handling Utilities ---

def extract_node_info(node) -> dict:
    """Extract node info to be used in the DataFrame."""
    g = node.group if hasattr(node, "group") else Group(names=["__NO_GROUP__"])
    full_name = node.__name__
    short_name = full_name[len("_".join(g.names)) + 1:] if g.names else full_name
    return {
        "name": short_name,
        "full_name": full_name,
        "group": tuple(g.names),
        "changed": False  # Placeholder for change detection
    }


def try_load_node(args: tuple) -> dict | None:
    """Attempt to load a node from a remote/revision."""
    node_address, remote, rev = args
    try:
        node = zntrack.from_rev(name=node_address, remote=remote, rev=rev)
        return extract_node_info(node)
    except (ModuleNotFoundError, ValueError):
        return None


# --- Node Listing & Execution ---

def list_nodes(remote: str | None = None, rev: str | None = None) -> pd.DataFrame:
    """List nodes from a DVC repository."""
    fs = dvc.api.DVCFileSystem(url=remote, rev=rev)
    nodes: list[Stage | PipelineStage] = list(fs.repo.stage.collect())
    print(f"Found {len(nodes)} nodes in the DVC graph.")

    node_data = []

    for node in nodes:
        if isinstance(node, PipelineStage):
            try:
                config_path = Path(node.path_in_repo).parent / "zntrack.json"
                config = json.loads(fs.read_text(config_path))
                nwd = config[node.name]["nwd"]["value"]
                g = Group.from_nwd(Path(nwd))
                full_name = node.name
                if g is not None:
                    short_name = full_name[len("_".join(g.names)) + 1:] if g.names else full_name
                else:
                    short_name = full_name

                node_data.append({
                    "name": short_name,
                    "full_name": full_name,
                    "group": tuple(g.names) if g is not None else ("__NO_GROUP__",),
                    "changed": False
                })
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                print(f"Failed to parse node config: {e}")

    df = pd.DataFrame(node_data)

    # Optional: Render the tree view
    console = Console()
    for top_tree in build_forest(df):
        console.print(top_tree)

    return df