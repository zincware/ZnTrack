# server.py

import dataclasses
import importlib.metadata
import inspect
import sys
from collections import defaultdict
from pathlib import Path
from typing import Protocol, get_type_hints

from fastmcp import FastMCP

from zntrack.config import FIELD_TYPE
from zntrack.entrypoints import get_registered_nodes

mcp = FastMCP("ZnTrack 🚀")

@mcp.tool
def get_graph_getting_started() -> str:
    """Get documentation on how to build a graph."""
    file = Path(__file__).parent / "resources" / "graph_getting_started.md"
    return file.read_text()

@mcp.tool
def get_graph_with_groups() -> str:
    """Get documentation on how to build a graph with groups."""
    file = Path(__file__).parent / "resources" / "graph_with_groups.md"
    return file.read_text()

@mcp.tool
def get_node_getting_started() -> str:
    """Get documentation on how to use ZnTrack nodes."""
    file = Path(__file__).parent / "resources" / "node_getting_started.md"
    return file.read_text()

@mcp.tool
def get_package_info() -> dict[str, str]:
    """Get all packages that provide ZnTrack Nodes."""
    nodes = get_registered_nodes("zntrack.nodes")
    # get package description
    package_info = {}
    for package, _ in nodes.items():
        try:
            metadata = importlib.metadata.metadata(package)
            package_info[package] = metadata.get("Summary", "No description available.")
        except importlib.metadata.PackageNotFoundError:
            package_info[package] = "Package not found."

    return package_info

@mcp.tool
def get_node_list(package: str) -> list[str]:
    """Get all nodes provided by a specific package."""
    nodes = get_registered_nodes("zntrack.nodes")
    if package not in nodes:
        return [f"Package '{package}' not found."]
    return sorted(nodes[package])

@mcp.tool
def get_interfaces_list(package: str) -> list[str]:
    """Get interfaces that define how nodes can interact with each other."""
    interfaces = get_registered_nodes(group="zntrack.interfaces")
    if package not in interfaces:
        return [f"Package '{package}' not found."]
    return sorted(interfaces[package])

@mcp.tool
def get_interface_info(package: str, interface: str) -> dict:
    """Get the source code of a specific ZnTrack interface."""
    interfaces = get_registered_nodes(group="zntrack.interfaces")
    if package not in interfaces or interface not in interfaces[package]:
        return {"error": f"Interface '{interface}' not found in package '{package}'."}

    try:
        module = importlib.import_module(f"{package}.interfaces")
        interface_class = getattr(module, interface)
        source = inspect.getsource(interface_class)
        return {
            "source": source,
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def get_node_info(package: str, node: str, detailed: bool = False) -> dict:
    """Get information about a specific ZnTrack node.
    
    Parameters
    ----------
    package : str
        The package name, e.g. "ipsuite"
    node : str
        The node class name, e.g. "ASEGeoOpt"
    detailed : bool
        If True, include detailed information about fields and methods.
    """
    try:
        module = importlib.import_module(package)
        node_class = getattr(module, node)
    except (ImportError, AttributeError) as e:
        return {"error": str(e)}

    docs = node_class.__doc__ or "No documentation available."
    if not detailed:
        return {
            "docs": docs,
            "name": node,
            "module": package,
        }
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
            return_type = get_type_hints(attr.fget).get("return", None)
            methods["properties"][attr_name] = repr(return_type)

        # Class methods
        elif inspect.ismethod(attr) and getattr(attr, "__self__", None) is node_class:
            return_type = get_type_hints(attr).get("return", None)
            methods["class_methods"][attr_name] = repr(return_type)

        # Static methods
        elif isinstance(inspect.getattr_static(node_class, attr_name), staticmethod):
            return_type = get_type_hints(attr).get("return", None)
            methods["static_methods"][attr_name] = repr(return_type)

        # Instance methods
        elif inspect.isfunction(attr):
            return_type = get_type_hints(attr).get("return", None)
            methods["instance_methods"][attr_name] = repr(return_type)

    return {
        "docs": docs,
        "name": node,
        "module": package,
        "fields": fields_by_type,
        "methods": methods,
    }


@mcp.tool
def get_docs_diffusion() -> str:
    """Additional information when computing self diffusion."""
    return "It is important to run the simulation long enough. For water, at least 1 ns, for more viscous liquids, up to 50 ns or more "

# @mcp.resource("docs://build-workflow")
# def build_workflow() -> list[str]:
#     """How to build a workflow with ZnTrack nodes."""
#     # TODO: setup a git repository, uv / git / dvc init ...
#     steps = [
#         "check how zntrack graphs work via 'get_graph_getting_started'",
#         "list all available packages that export nodes in the current environment via 'get_package_info'",
#         "list all available nodes in a specific package that suites the task via 'get_node_list'",
#         "select nodes that fit and get their information via 'get_node_info'",
#         "propose a workflow by connecting nodes together",
#         "check if the workflows complexity justifies using groups via 'get_graph_with_groups'",
#     ]
#     return steps

# def analyze_node(path: str, name: str) -> dict:
#     module = importlib.import_module(path)
#     node_class = getattr(module, name)
#     docs = node_class.__doc__

#     fields_by_type = defaultdict(list)
#     type_hints = get_type_hints(node_class)

#     # Collect dataclass field names
#     dataclass_field_names = {f.name for f in dataclasses.fields(node_class)}
#     for field in dataclasses.fields(node_class):
#         field_type = field.metadata.get(FIELD_TYPE)
#         if field_type is not None:
#             hint = type_hints.get(field.name, None)
#             fields_by_type[field_type].append((field.name, repr(hint)))

#     # Collect other members
#     methods = {
#         "instance_methods": {},
#         "class_methods": {},
#         "static_methods": {},
#         "properties": {},
#     }

#     for attr_name, attr in inspect.getmembers(node_class):
#         if attr_name.startswith("__") or attr_name in dataclass_field_names:
#             continue

#         # Properties
#         if isinstance(attr, property):
#             return_type = get_type_hints(attr.fget).get("return", None)
#             methods["properties"][attr_name] = repr(return_type)

#         # Class methods
#         elif inspect.ismethod(attr) and getattr(attr, "__self__", None) is node_class:
#             return_type = get_type_hints(attr).get("return", None)
#             methods["class_methods"][attr_name] = repr(return_type)

#         # Static methods
#         elif isinstance(inspect.getattr_static(node_class, attr_name), staticmethod):
#             return_type = get_type_hints(attr).get("return", None)
#             methods["static_methods"][attr_name] = repr(return_type)

#         # Instance methods
#         elif inspect.isfunction(attr):
#             return_type = get_type_hints(attr).get("return", None)
#             methods["instance_methods"][attr_name] = repr(return_type)

#     return {
#         "docs": docs,
#         "name": name,
#         "module": path,
#         "fields": fields_by_type,
#         "methods": methods,
#     }



# @mcp.tool
# def check_interface(interface_path: str, interface_name: str) -> dict[str, bool]:
#     """Check all available nodes that implement a specific interface."""
#     """Check all available nodes that implement a specific interface."""
#     interface_module = importlib.import_module(interface_path)
#     interface_class = getattr(interface_module, interface_name)

#     supported_nodes = {}

#     if not isinstance(interface_class, type) or not issubclass(interface_class, Protocol):
#         raise TypeError(f"{interface_name} is not a Protocol.")

#     # Get required method names from the protocol
#     required_attrs = {
#         name: attr
#         for name, attr in interface_class.__dict__.items()
#         if callable(attr) and not name.startswith("_")
#     }

#     registered_nodes = get_registered_nodes()
#     # TODO: this might not be correct all the time. E.g. `ipsuite.MACEMPModel` has `HasAtoms` altough it should not
#     for module_name, node_names in registered_nodes.items():
#         for node_name in node_names:
#             full_name = f"{module_name}.{node_name}"
#             try:
#                 node_module = importlib.import_module(module_name)
#                 node_class = getattr(node_module, node_name)

#                 # Check that all protocol methods exist and are callable
#                 if not all(
#                     hasattr(node_class, name) and callable(getattr(node_class, name))
#                     for name in required_attrs
#                 ):
#                     continue

#                 for name, proto_func in required_attrs.items():
#                     proto_sig = inspect.signature(proto_func)
#                     node_func = getattr(node_class, name, None)

#                     if node_func is None:
#                         continue

#                     try:
#                         node_sig = inspect.signature(node_func)
#                     except ValueError:
#                         continue

#                     # You can go deeper here: check param names/types/return type compatibility
#                     # For now, we just check that all parameters are present
#                     if len(proto_sig.parameters) > len(node_sig.parameters):
#                         continue

#                 supported_nodes[full_name] = True

#             except Exception:
#                 pass

#     return supported_nodes


# @mcp.tool
# def available_nodes() -> dict[str, list[str]]:
#     """Get all available ZnTrack nodes in the current environment.

#     The nodes are sorted by their module names.
#     """
#     from zntrack.entrypoints import get_registered_nodes

#     return get_registered_nodes()


# @mcp.tool
# def node_info(path: str, name: str) -> dict:
#     """Get information about a specific ZnTrack node.

#     Attributes
#     ----------
#     path : str
#         The module path of the node, e.g. "zntrack.examples"
#     name : str
#         The name of the node, e.g. "ParamsToOuts"

#     """
#     try:
#         return analyze_node(path, name)
#     except (ImportError, AttributeError) as e:
#         return {"error": str(e)}


# @mcp.tool
# def zntrack_documentation() -> dict[str, str]:
#     """Get resources on how to build a graph."""
#     return {
#         "How to build a graph": "docs://graph/getting-started",
#         "How to include groups into a graph": "docs://graph/with-groups",
#         "How to write a custom node": "docs://node/getting-started",
#     }


# @mcp.resource("docs://graph/getting-started")
# def graph_getting_started() -> str:
#     """Get documentation on how to build a graph."""
#     file = Path(__file__).parent / "resources" / "graph_getting_started.md"
#     return file.read_text()


# @mcp.resource("docs://graph/with-groups")
# def graph_with_groups() -> str:
#     """Get documentation on how to build a graph with groups."""
#     file = Path(__file__).parent / "resources" / "graph_with_groups.md"
#     return file.read_text()


# @mcp.resource("docs://node/getting-started")
# def node_getting_started() -> str:
#     """Get documentation on how to use ZnTrack nodes."""
#     file = Path(__file__).parent / "resources" / "node_getting_started.md"
#     return file.read_text()


# @mcp.tool
# def get_project_groups(project_dir: str) -> list[tuple[str, ...]]:
#     """List all groups that are in the current project.
#     Group names are tuples of nested groups, like ('group1', 'subgroup1').

#     Parameters
#     ----------
#     project_dir : str
#         The (absolute)path to "main.py" file containing "project = zntrack.Project()" instance.
#     """
#     sys.path.insert(0, project_dir)
#     from main import project

#     return list(project.groups.keys())


# @mcp.tool
# def get_all_nodes(project_dir: str) -> list[str]:
#     """List all nodes in the current project.

#     Parameters
#     ----------
#     project_dir : str
#         The (absolute)path to "main.py" file containing "project = zntrack.Project()" instance.
#     """
#     sys.path.insert(0, project_dir)
#     from main import project

#     return [x["value"].name for _, x in project.nodes(data=True)]


# @mcp.tool
# def get_nodes_in_group(group: tuple[str, ...], project_dir: str) -> dict:
#     """List all nodes in a specific group."""

#     sys.path.insert(0, project_dir)
#     from main import project

#     try:
#         node_names = [project.nodes[x]["value"].name for x in project.groups[group].uuids]
#         return {"group": group, "nodes": node_names}
#     except KeyError:
#         return {"error": f"Group {group} not found."}


# @mcp.tool
# def get_connections(name: str, project_dir: str) -> dict:
#     """Get all connections for a specific node."""
#     sys.path.insert(0, project_dir)
#     from main import project

#     node_uuid = [uuid for uuid, x in project.nodes(data=True) if x["value"].name == name][
#         0
#     ]
#     if not node_uuid:
#         return {"error": f"Node {name} not found."}
#     successors_uuid = list(project.successors(node_uuid))
#     predecessors_uuid = list(project.predecessors(node_uuid))

#     successors = [project.nodes[uuid]["value"].name for uuid in successors_uuid]
#     predecessors = [project.nodes[uuid]["value"].name for uuid in predecessors_uuid]

#     return {
#         "node": name,
#         "successors": successors,
#         "predecessors": predecessors,
#     }


# @mcp.tool
# def get_node_by_name(name: str, project_dir: str) -> dict:
#     """Get a node by its name."""
#     import zntrack

#     try:
#         node = zntrack.from_rev(name, remote=project_dir)
#     except Exception as e:
#         return {"error": str(e)}
#     return {
#         "cls": node.__class__.__name__,
#         "module": node.__module__,
#     }

if __name__ == "__main__":
    mcp.run()
