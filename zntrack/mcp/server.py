# server.py

import sys
from fastmcp import FastMCP
from collections import defaultdict

import importlib
import dataclasses
import inspect
from typing import get_type_hints, Protocol
from pathlib import Path

import importlib
import dataclasses
from zntrack.config import FIELD_TYPE
from typing import get_type_hints
import importlib
from zntrack.entrypoints import get_registered_nodes

mcp = FastMCP("ZnTrack 🚀")

def analyze_node(path: str, name: str) -> dict:
    module = importlib.import_module(path)
    node_class = getattr(module, name)
    docs = node_class.__doc__
    
    fields_by_type = defaultdict(list)
    type_hints = get_type_hints(node_class)

    # Collect dataclass field names
    dataclass_field_names = {f.name for f in dataclasses.fields(node_class)}
    for field in dataclasses.fields(node_class):
        field_type = field.metadata.get(FIELD_TYPE)
        if field_type is not None:
            hint = type_hints.get(field.name, None)
            fields_by_type[field_type].append((field.name, repr(hint)))

    # Collect other members
    methods = {
        "instance_methods": {},
        "class_methods": {},
        "static_methods": {},
        "properties": {},
    }

    for attr_name, attr in inspect.getmembers(node_class):
        if attr_name.startswith("__") or attr_name in dataclass_field_names:
            continue

        # Properties
        if isinstance(attr, property):
            return_type = get_type_hints(attr.fget).get('return', None)
            methods["properties"][attr_name] = repr(return_type)

        # Class methods
        elif inspect.ismethod(attr) and getattr(attr, "__self__", None) is node_class:
            return_type = get_type_hints(attr).get('return', None)
            methods["class_methods"][attr_name] = repr(return_type)

        # Static methods
        elif isinstance(inspect.getattr_static(node_class, attr_name), staticmethod):
            return_type = get_type_hints(attr).get('return', None)
            methods["static_methods"][attr_name] = repr(return_type)

        # Instance methods
        elif inspect.isfunction(attr):
            return_type = get_type_hints(attr).get('return', None)
            methods["instance_methods"][attr_name] = repr(return_type)

    return {
        "docs": docs,
        "name": name,
        "module": path,
        "fields": fields_by_type,
        "methods": methods,
    }

@mcp.tool
def get_interfaces() -> dict[str, list[str]]:
    """Get all available ZnTrack interfaces in the current environment.
    
    The interfaces are sorted by their module names.
    """
    return get_registered_nodes(group="zntrack.interfaces")


@mcp.tool
def check_interface(interface_path: str, interface_name: str) -> dict[str, bool]:
    """Check all available nodes that implement a specific interface."""
    """Check all available nodes that implement a specific interface."""
    interface_module = importlib.import_module(interface_path)
    interface_class = getattr(interface_module, interface_name)

    supported_nodes = {}

    if not isinstance(interface_class, type) or not issubclass(interface_class, Protocol):
        raise TypeError(f"{interface_name} is not a Protocol.")

    # Get required method names from the protocol
    required_attrs = {
        name: attr
        for name, attr in interface_class.__dict__.items()
        if callable(attr) and not name.startswith("_")
    }

    registered_nodes = get_registered_nodes()
    # TODO: this might not be correct all the time. E.g. `ipsuite.MACEMPModel` has `HasAtoms` altough it should not
    for module_name, node_names in registered_nodes.items():
        for node_name in node_names:
            full_name = f"{module_name}.{node_name}"
            try:
                node_module = importlib.import_module(module_name)
                node_class = getattr(node_module, node_name)

                # Check that all protocol methods exist and are callable
                if not all(hasattr(node_class, name) and callable(getattr(node_class, name))
                           for name in required_attrs):
                    continue

                for name, proto_func in required_attrs.items():
                    proto_sig = inspect.signature(proto_func)
                    node_func = getattr(node_class, name, None)

                    if node_func is None:
                        continue

                    try:
                        node_sig = inspect.signature(node_func)
                    except ValueError:
                        continue

                    # You can go deeper here: check param names/types/return type compatibility
                    # For now, we just check that all parameters are present
                    if len(proto_sig.parameters) > len(node_sig.parameters):
                        continue

                supported_nodes[full_name] = True

            except Exception:
                pass

    return supported_nodes

@mcp.tool
def available_nodes() -> dict[str, list[str]]:
    """Get all available ZnTrack nodes in the current environment.
    
    The nodes are sorted by their module names.
    """
    from zntrack.entrypoints import get_registered_nodes
    return get_registered_nodes()
 

@mcp.tool
def node_info(path: str, name: str) -> dict:
    """Get information about a specific ZnTrack node.
    
    Attributes
    ----------
    path : str
        The module path of the node, e.g. "zntrack.examples"
    name : str
        The name of the node, e.g. "ParamsToOuts"
    
    """
    try:
        return analyze_node(path, name)
    except (ImportError, AttributeError) as e:
        return {"error": str(e)}


@mcp.tool
def zntrack_documentation() -> dict[str, str]:
    """Get resources on how to build a graph."""
    return {
        "How to build a graph": "docs://graph/getting-started",
        "How to include groups into a graph": "docs://graph/with-groups",
        "How to write a custom node": "docs://node/getting-started",
    }


@mcp.resource("docs://graph/getting-started")
def graph_getting_started() -> str:
    """Get documentation on how to build a graph."""
    file = Path(__file__).parent / "resources" / "graph_getting_started.md"
    return file.read_text()

@mcp.resource("docs://graph/with-groups")
def graph_with_groups() -> str:
    """Get documentation on how to build a graph with groups."""
    file = Path(__file__).parent / "resources" / "graph_with_groups.md"
    return file.read_text()

@mcp.resource("docs://node/getting-started")
def node_getting_started() -> str:
    """Get documentation on how to use ZnTrack nodes."""
    file = Path(__file__).parent / "resources" / "node_getting_started.md"
    return file.read_text()


@mcp.tool
def get_project_groups(project_dir: str) -> list[tuple[str, ...]]:
    """List all groups that are in the current project.
    Group names are tuples of nested groups, like ('group1', 'subgroup1').

    Parameters
    ----------
    project_dir : str
        The (absolute)path to "main.py" file containing "project = zntrack.Project()" instance.
    """
    sys.path.insert(0, project_dir)
    from main import project

    return list(project.groups.keys())

@mcp.tool
def get_all_nodes(project_dir: str) -> list[str]:
    """List all nodes in the current project.

    Parameters
    ----------
    project_dir : str
        The (absolute)path to "main.py" file containing "project = zntrack.Project()" instance.
    """
    sys.path.insert(0, project_dir)
    from main import project

    return [x["value"].name for _, x in project.nodes(data=True)]

@mcp.tool
def get_nodes_in_group(group: tuple[str, ...], project_dir: str) -> dict:
    """List all nodes in a specific group."""

    sys.path.insert(0, project_dir)
    from main import project

    try:
        node_names = [project.nodes[x]["value"].name for x in project.groups[group].uuids]
        return {"group": group,
                "nodes": node_names}
    except KeyError:
        return {"error": f"Group {group} not found."}
    
@mcp.tool
def get_connections(name: str, project_dir: str) -> dict:
    """Get all connections for a specific node."""
    sys.path.insert(0, project_dir)
    from main import project

    node_uuid = [uuid for uuid, x in project.nodes(data=True) if x["value"].name == name][0]
    if not node_uuid:
        return {"error": f"Node {name} not found."}
    successors_uuid = list(project.successors(node_uuid))
    predecessors_uuid = list(project.predecessors(node_uuid))

    successors = [project.nodes[uuid]["value"].name for uuid in successors_uuid]
    predecessors = [project.nodes[uuid]["value"].name for uuid in predecessors_uuid]

    return {
        "node": name,
        "successors": successors,
        "predecessors": predecessors,
    }

@mcp.tool
def get_node_by_name(name: str, project_dir: str) -> dict:
    """Get a node by its name."""
    import zntrack
    try:
        node = zntrack.from_rev(name, remote=project_dir)
    except Exception as e:
        return {"error": str(e)}
    return {
        "cls": node.__class__.__name__,
        "module": node.__module__,
    }
