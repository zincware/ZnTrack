import logging

import yaml
import znflow
import znjson

from . import config, converter

log = logging.getLogger(__name__)


class Project(znflow.DiGraph):
    def add_node(self, node_for_adding, **attr):
        return super().add_node(node_for_adding, **attr)

    def __exit__(self, exc_type, exc_val, exc_tb):
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
