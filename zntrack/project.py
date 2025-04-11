import contextlib
import json
import logging
import os
import pathlib
import subprocess
import warnings

import git
import tqdm
import yaml
import znflow

from zntrack import utils
from zntrack.config import NWD_PATH
from zntrack.group import Group
from zntrack.state import PLUGIN_LIST
from zntrack.utils.finalize import make_commit
from zntrack.utils.import_handler import import_handler
from zntrack.utils.misc import load_env_vars

from . import config
from .deployment import ZnTrackDeployment

log = logging.getLogger(__name__)


class _FinalNodeNameString(str):
    """A string that represents the final name of a node.

    Used to differentiate between a custom name and a computed name.
    """


class Project(znflow.DiGraph):
    def __init__(
        self,
        *args,
        disable=False,
        immutable_nodes=True,
        deployment=None,
        tags: dict[str, str] | None = None,
        **kwargs,
    ):
        if deployment is None:
            deployment = ZnTrackDeployment()
        self.tags = tags or {}
        load_env_vars()
        super().__init__(
            *args,
            disable=disable,
            immutable_nodes=immutable_nodes,
            deployment=deployment,
            **kwargs,
        )
        self.node_name_counter: dict[str, int] = {}
        # keep track of all nwd paths, they should be unique, until
        # https://github.com/zincware/ZnFlow/issues/132 can be used
        # to set nwd directly as pk

    def _get_updated_node_nwd(self, name: str) -> pathlib.Path:
        """
        Generate an updated node path within the working directory, ensuring uniqueness.

        If `active_group` is set, the path is nested within the group structure.
        Otherwise, the node name is managed at the root level.

        Parameters
        ----------
        name : str
            The base name of the node.

        Returns
        -------
        pathlib.Path
            The updated node path with an incremented counter if necessary.
        """
        if self.active_group is None:
            counter = self.node_name_counter.get(name, 0)
            self.node_name_counter[name] = counter + 1

            if counter:
                return NWD_PATH / f"{name}_{counter}"
            return NWD_PATH / name
        else:
            group_path = "/".join(self.active_group.names)
            grp_and_name = f"{group_path}/{name}"

            counter = self.node_name_counter.get(grp_and_name, 0)
            self.node_name_counter[grp_and_name] = counter + 1

            if counter:
                return NWD_PATH / group_path / f"{name}_{counter}"
            return NWD_PATH / group_path / name

    def add_znflow_node(self, node_for_adding, **attr):
        from zntrack import Node

        if not isinstance(node_for_adding, Node):
            raise ValueError(
                "Node must be an instance of 'zntrack.Node',"
                f" not {type(node_for_adding)}."
            )
        if node_for_adding._external_:
            return super().add_znflow_node(node_for_adding)
        # here we finalize the node name!
        # It can only be updated once more via `MyNode(name=...)`
        nwd = self._get_updated_node_nwd(node_for_adding.__class__.__name__)
        node_for_adding.__dict__["nwd"] = nwd

        return super().add_znflow_node(node_for_adding)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            for group in self.groups.values():
                for node_uuid in group.uuids:
                    # we need to access the `state` attribute to initialize
                    # the property, so the `log.debug` is necessary!
                    log.debug(self.nodes[node_uuid]["value"].state)
                    self.nodes[node_uuid]["value"].__dict__["state"]["group"] = (
                        Group.from_znflow_group(group)
                    )
        finally:
            super().__exit__(exc_type, exc_val, exc_tb)

    def build(self) -> None:
        log.info(f"Saving {config.PARAMS_FILE_PATH}")
        params_dict = {}
        dvc_dict = {"stages": {}, "plots": []}
        zntrack_dict = {}
        try:
            repo = git.Repo()
        except git.InvalidGitRepositoryError:
            repo = None
        for node_uuid in tqdm.tqdm(self):
            node = self.nodes[node_uuid]["value"]

            # check if the node.nwd / node-meta.json is git tracked
            if config.ALWAYS_CACHE and repo is not None:
                meta_file = node.nwd / "node-meta.json"
                # Convert to relative path safely
                rel_path = os.path.relpath(meta_file, repo.working_dir)

                # Check if the file is tracked
                is_tracked = rel_path in repo.git.ls_files()
                if is_tracked:
                    warnings.warn(
                        f"{meta_file} is tracked by git. Please set "
                        "`zntrack.config.ALWAYS_CACHE = False` or remove the "
                        "file from git. This has been changed with ZnTrack v0.8.4."
                        " Mixing git and DVC tracked stage outputs can"
                        " lead to unexpected behavior."
                    )

            if node._external_:
                continue
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
                    # TODO: this won't work if multiple
                    # plugins want to modify the dvc.yaml
                    if len(value["plots"]) > 0:
                        dvc_dict["plots"].extend(value["plots"])
                if (
                    value := plugin.convert_to_zntrack_json(graph=self)
                ) is not config.PLUGIN_EMPTY_RETRUN_VALUE:
                    zntrack_dict[node.name] = value

        if len(dvc_dict["plots"]) == 0:
            del dvc_dict["plots"]

        config.PARAMS_FILE_PATH.write_text(yaml.safe_dump(params_dict))
        config.DVC_FILE_PATH.write_text(yaml.safe_dump(dvc_dict))
        config.ZNTRACK_FILE_PATH.write_text(json.dumps(zntrack_dict, indent=4))

        # TODO: update file or overwrite?

    def repro(self, build: bool = True, force: bool = False):
        if build:
            self.build()
        cmd = ["dvc", "repro"]
        if force:
            cmd.append("--force")
        subprocess.check_call(cmd)

    def finalize(
        self,
        msg: str | None = None,
        commit: bool = True,
        skip_cached: bool = True,
        update_run_names: bool = True,
        **kwargs,
    ):
        """Finalize the project by making a commit and loading environment variables.

        This method performs the following actions:
        1. Makes a commit with the provided message if `commit` is True.
        2. Loads environment variables.
        3. Loads and finalizes plugins specified
           in the `ZNTRACK_PLUGINS` environment variable.

        Parameters
        ----------
        msg : str, optional
            The commit message. If None, the message will be 'zntrack: auto commit'.
        commit : bool, optional
            Whether to make a commit or not. Default is True
        skip_cached : bool, optional
            Do not upload cached nodes.
        update_run_names: bool, optional
            Include part of the commit message in the run names.
        **kwargs
            Additional keyword arguments to pass to `make_commit`.

        """
        if msg is None:
            msg = "zntrack: auto commit"
        if commit:
            make_commit(msg, **kwargs)
        utils.misc.load_env_vars()
        plugins_paths = os.environ.get(
            "ZNTRACK_PLUGINS", "zntrack.plugins.dvc_plugin.DVCPlugin"
        )
        plugins: PLUGIN_LIST = [import_handler(p) for p in plugins_paths.split(",")]
        for plugin in plugins:
            plugin.finalize(skip_cached=skip_cached, update_run_names=update_run_names)

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
            while (name,) in self.groups:
                name = f"Group{int(name[5:]) + 1}"
            names = (name,)
        else:
            if any("_" in name for name in names):
                warnings.warn(
                    "Group name should not contain '_'. "
                    f"Consider using '-' instead for {','.join(names)}."
                )

        with super().group(*names) as znflow_grp:
            group = Group(names=znflow_grp.names)
            yield group
        group._nodes = znflow_grp.nodes
