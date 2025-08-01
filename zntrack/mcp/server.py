# server.py
import json
import subprocess
from typing import Any, List

from fastmcp import FastMCP
from pydantic import BaseModel


class NodeDict(BaseModel):
    id: dict[str, str]


class LinkDict(BaseModel):
    source: dict[str, str]
    target: dict[str, str]
    # Other optional edge attributes, e.g., weight
    # Same here: total=False for flexibility


class NodeLinkData(BaseModel):
    directed: bool
    multigraph: bool
    graph: dict[str, Any]  # Metadata about the whole graph (usually empty)
    nodes: List[NodeDict]
    edges: List[LinkDict]


mcp = FastMCP("ZnTrack 🚀")


@mcp.tool
def status(name: str | None = None) -> dict[str, list[dict]]:
    """Check if any Node in the workflow is not up-to-date."""
    if name:
        result = subprocess.run(
            ["dvc", "status", "--json", name], capture_output=True, text=True
        )
    else:
        result = subprocess.run(
            ["dvc", "status", "--json"], capture_output=True, text=True
        )
    return json.loads(result.stdout)


@mcp.tool
def graph() -> NodeLinkData:
    """Get the workflow graph in node-link format."""
    import dvc.api
    import znjson
    from dvc.stage import PipelineStage
    from networkx.readwrite import json_graph

    class PipelineStageConverter(znjson.ConverterBase):
        instance: type = PipelineStage
        representation: str = "dvc.stage.PipelineStage"

        def encode(self, obj: PipelineStage) -> str:
            return obj.addressing

        def decode(self, value: str) -> PipelineStage:
            raise NotImplementedError("Decoding PipelineStage is not implemented")

    fs = dvc.api.DVCFileSystem()
    graph = fs.repo.index.graph
    return json.loads(
        json.dumps(
            json_graph.node_link_data(graph, edges="edges"),
            cls=znjson.ZnEncoder.from_converters([PipelineStageConverter]),
        )
    )


@mcp.tool
def node_info(node: str) -> dict:
    """Get information about a specific node in the workflow, including class source if it's a zntrack node."""
    import importlib
    import inspect
    import shlex

    import dvc.api

    # Load DVC graph
    fs = dvc.api.DVCFileSystem()
    graph = fs.repo.index.graph

    # Find the node by name
    matching_nodes = [x for x in graph.nodes if x.addressing == node]
    if not matching_nodes:
        return {"error": f"Node '{node}' not found."}

    dvc_node = matching_nodes[0]
    cmd = dvc_node.cmd

    # Parse command with shlex to properly split quoted args etc.
    parts = shlex.split(cmd)

    if len(parts) >= 3 and parts[0] == "zntrack" and parts[1] == "run":
        class_path = parts[2]
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            source = inspect.getsource(cls)
            return {
                "node": node,
                "cmd": cmd,
                "module": module_path,
                "class": class_name,
                "source": source,
            }
        except Exception as e:
            return {
                "node": node,
                "cmd": cmd,
                "error": f"Failed to import or inspect class: {e}",
            }

    return {
        "node": node,
        "cmd": cmd,
        "info": "Command is not a recognized 'zntrack run <Class>' pattern.",
    }


@mcp.tool
def node_results(node: str, attr: str) -> dict:
    """Get the value of a specific attribute from a zntrack node."""
    import zntrack

    instance = zntrack.from_rev(node)
    if not hasattr(instance, attr):
        return {"error": f"Node '{node}' does not have attribute '{attr}'."}

    value = getattr(instance, attr)
    return {"repr": repr(value), "type": str(type(value))}


@mcp.tool
def run_node(node: str | None = None) -> dict:
    """Run a specific node."""
    import subprocess

    if node is None:
        result = subprocess.run(["dvc", "repro"], capture_output=True, text=True)
    else:
        result = subprocess.run(["dvc", "repro", node], capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": f"Failed to run node '{node}': {result.stderr}"}

    return {"message": f"Node '{node}' executed successfully.", "output": result.stdout}
