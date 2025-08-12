"""Entry points discovery for ZnTrack nodes.

This module provides functionality to discover and load all packages
that have registered entry points under 'zntrack.nodes'.
"""

import importlib
import importlib.metadata
import logging
from collections import defaultdict

log = logging.getLogger(__name__)
def get_registered_nodes(group: str = "zntrack.nodes") -> dict[str, list[str]]:
    """Get all packages that registered into [project.entry-points.'zntrack.nodes']."""
    registered_nodes = defaultdict(list)

    try:
        # Get all entry points for the 'zntrack.nodes' group
        entry_points = importlib.metadata.entry_points(group=group)

        for entry_point in entry_points:
            try:
                # Load the function registered at this entry point
                nodes_func = entry_point.load()

                # Call the function to get the dictionary of module -> node names
                nodes_dict = nodes_func()

                for module_name, node_names in nodes_dict.items():
                    module_name = module_name.replace("-", "_")  # Normalize module names
                    registered_nodes[module_name].extend(node_names)

            except Exception as e:
                log.error(f"Failed to load entry point '{entry_point.name}': {e}")
                continue

    except Exception as e:
        log.error(f"Failed to discover entry points: {e}")

    return dict(registered_nodes)
