import contextlib
import logging
import pathlib

import yaml
import znflow
import znjson

from . import config, converter
from .deployment import ZnTrackDeployment

log = logging.getLogger(__name__)


class Project(znflow.DiGraph):
    def __init__(
        self, *args, disable=False, immutable_nodes=True, deployment=None, **kwargs
    ):
        if deployment is None:
            deployment = ZnTrackDeployment()
        super().__init__(
            *args,
            disable=disable,
            immutable_nodes=immutable_nodes,
            deployment=deployment,
            **kwargs,
        )

    def add_node(self, node_for_adding, **attr):
        from zntrack import Node

        if not isinstance(node_for_adding, Node):
            raise ValueError(
                f"Node must be an instance of 'zntrack.Node', not {type(node_for_adding)}"
            )

        return super().add_node(node_for_adding, **attr)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for group in self.groups:
            for node in self.groups[group]:
                # we need to access the `state` attribute to initialize
                # the property, so the `log.debug` is necessary!
                log.debug(self.nodes[node]["value"].state)
                self.nodes[node]["value"].__dict__["state"]["group"] = group

        # need to fix the node names
        all_nodes = [self.nodes[uuid]["value"] for uuid in self.nodes]
        for node in all_nodes:
            if node.name is None:
                node_name = node.__class__.__name__
                if node_name not in [n.name for n in all_nodes]:
                    node.name = node_name
                else:
                    i = 0
                    while True:
                        i += 1
                        if f"{node_name}_{i}" not in [n.name for n in all_nodes]:
                            node.name = f"{node_name}_{i}"
                            break
        return super().__exit__(exc_type, exc_val, exc_tb)

    def build(self) -> None:
        log.info(f"Saving {config.PARAMS_FILE_PATH}")
        # TODO: update file or overwrite?
        config.PARAMS_FILE_PATH.write_text(
            yaml.safe_dump(converter.convert_graph_to_parameter(self))
        )
        log.info(f"Saving {config.DVC_FILE_PATH}")
        config.DVC_FILE_PATH.write_text(
            yaml.safe_dump(converter.convert_graph_to_dvc_config(self))
        )
        log.info(f"Saving {config.ZNTRACK_FILE_PATH}")
        config.ZNTRACK_FILE_PATH.write_text(
            znjson.dumps(
                converter.convert_graph_to_zntrack_config(self),
                indent=4,
                cls=znjson.ZnEncoder.from_converters(
                    [converter.ConnectionConverter, converter.NodeConverter],
                    add_default=True,
                ),
            )
        )

    @contextlib.contextmanager
    def group(self, *names: str):
        """Group nodes together.

        Parameters
        ----------
        names : list[str], optional
            The name of the group. If None, the group will be named 'GroupX' where X is
            the number of groups + 1. If more than one name is given, the groups will
            be nested to 'nwd = name[0]/name[1]/.../name[-1]'

        """
        if not names:
            name = "Group1"
            while pathlib.Path("nodes", name).exists():
                name = f"Group{int(name[5:]) + 1}"
            names = (name,)

        with super().group(*names) as group:
            yield group
