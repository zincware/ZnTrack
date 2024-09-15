import contextlib
import json
import logging
import pathlib
import subprocess

import tqdm
import yaml
import znflow

from zntrack.config import NWD_PATH
from zntrack.group import Group

from . import config
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
        for group in self.groups.values():
            for node_uuid in group.uuids:
                # we need to access the `state` attribute to initialize
                # the property, so the `log.debug` is necessary!
                log.debug(self.nodes[node_uuid]["value"].state)
                self.nodes[node_uuid]["value"].__dict__["state"]["group"] = (
                    Group.from_znflow_group(group)
                )

        # need to fix the node names
        all_nodes = [self.nodes[uuid]["value"] for uuid in self.nodes]
        all_node_names = [node.name for node in all_nodes]
        # TODO: accessing `node.name` should be instant, so this workaround
        # should not be required! Find and fix why it is slow!
        for node in tqdm.tqdm(all_nodes, desc="Collecting node names"):
            if node.name is None:
                if node.state.group is None:
                    node_name = node.__class__.__name__
                else:
                    node_name = node.state.group.get_node_name(node)
                if node_name not in all_node_names:
                    node.name = node_name
                    all_node_names.append(node_name)
                else:
                    i = 0
                    while True:
                        i += 1
                        if f"{node_name}_{i}" not in all_node_names:
                            node.name = f"{node_name}_{i}"
                            all_node_names.append(f"{node_name}_{i}")
                            break
        return super().__exit__(exc_type, exc_val, exc_tb)

    def build(self) -> None:
        log.info(f"Saving {config.PARAMS_FILE_PATH}")
        params_dict = {}
        dvc_dict = {"stages": {}, "plots": []}
        zntrack_dict = {}
        for node_uuid in tqdm.tqdm(self):
            node = self.nodes[node_uuid]["value"]
            for plugin in node.state.plugins.values():
                # TODO: combine all params into one dict
                if (
                    value := plugin.convert_to_params_yaml()
                ) is not config.PLUGIN_EMPTY_RETRUN_VALUE:
                    params_dict[node.name] = value
                if (
                    value := plugin.convert_to_dvc_yaml()
                ) is not config.PLUGIN_EMPTY_RETRUN_VALUE:
                    dvc_dict["stages"][node.name] = value["stages"]
                    if len(value["plots"]) > 0:
                        dvc_dict["plots"].extend(value["plots"])
                if (
                    value := plugin.convert_to_zntrack_json()
                ) is not config.PLUGIN_EMPTY_RETRUN_VALUE:
                    zntrack_dict[node.name] = value

        if len(dvc_dict["plots"]) == 0:
            del dvc_dict["plots"]

        log.info(f"Saving {params_dict = }")
        config.PARAMS_FILE_PATH.write_text(yaml.safe_dump(params_dict))
        config.DVC_FILE_PATH.write_text(yaml.safe_dump(dvc_dict))
        config.ZNTRACK_FILE_PATH.write_text(json.dumps(zntrack_dict, indent=4))

        # TODO: update file or overwrite?

    def repro(self, build: bool = True, force: bool = False):
        if build:
            self.build()
        if force:
            subprocess.check_call(["dvc", "repro", "-f"])
        subprocess.check_call(["dvc", "repro"])

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
        # This context manager also open self.__enter__ in the `super`
        if not names:
            name = "Group1"
            while pathlib.Path(NWD_PATH, name).exists():
                name = f"Group{int(name[5:]) + 1}"
            names = (name,)

        with super().group(*names) as znflow_grp:
            group = Group(name=znflow_grp.names)
            yield group
        group._nodes = znflow_grp.nodes
