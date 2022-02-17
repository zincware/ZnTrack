"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Node parameter
"""
from __future__ import annotations

import logging
import pathlib
import typing

from zntrack import descriptor, utils

log = logging.getLogger(__name__)


def uses_node_name(zntrack_type, instance) -> typing.Union[str, None]:
    """Check if the given metadata is associated with using the node_name as dict key

    Everything in nodes/<node_name>/ does not need it as key, because the directory
    is already named after the node. On the other side, parameters for example
    require the usage of node_name as a key inside the params.yaml file.

    Parameters
    ----------
    zntrack_type: str
    instance:
        Any instance object with the node_name attribute

    Returns
    -------
    str
        returns the node_name if it is being used, otherwise returns None

    """
    if zntrack_type in [utils.ZnTypes.results, utils.ZnTypes.metadata]:
        return None
    return instance.node_name


class ZnTrackOption(descriptor.Descriptor):
    """Descriptor for all DVC options

    This class handles the __get__ and __set__ for the DVC options.
    For most cases this means storing them in the __init__ and keeping track of,
    which Options are used.
    This is required to allow for load=True which updates all ZnTrackOptions,
    based on the computed or otherwise stored values.

    Attributes
    ----------
    file: str
        Either the zntrack file or the parameter file
    value_tracked: bool
        this is true if the getattr(instance, self.name) is an affected file,
         e.g. the dvc.<outs> is a file / list of files
    tracked: bool
        this is true if the internal file, such as in the case of zn.outs()
        like nodes/<node_name>/outs.json is an affected file

    """

    file = None
    value_tracked = False
    tracked = False
    dvc_option = ""
    zntrack_type = ""

    @property
    def dvc_args(self):
        return self.dvc_option.replace("_", "-")

    def __repr__(self):
        return f"{self.__class__}({hex(id(self))}) for <{self.dvc_option}>"

    def __str__(self):
        return f"{self.dvc_option} / {self.name}"

    def update_default(self):
        """Update default_value

        The default value is created upton instantiation of this descriptor,
        if a new class is created via Instance.load() it does not automatically load
        the default_value Nodes, so we must to this manually here
        """
        if isinstance(self.default_value, (list, tuple)):
            for value in self.default_value:
                # cheap trick because circular imports - TODO find clever fix!
                if hasattr(value, "update_options"):
                    value.update_options()
        else:
            if hasattr(self.default_value, "update_options"):
                self.default_value.update_options()

    def get_filename(self, instance) -> pathlib.Path:
        """Get the name of the file this ZnTrackOption will save its values to"""
        if uses_node_name(self.zntrack_type, instance) is None:
            return pathlib.Path("nodes", instance.node_name, f"{self.dvc_option}.json")
        return pathlib.Path(self.file)

    def save(self, instance):
        """Save this descriptor for the given instance to file

        Parameters
        ----------
        instance: Node
            instance where the Descriptor is attached to.
            Similar to __get__(instance) this requires the instance
            to be passed manually.
        """
        utils.file_io.update_config_file(
            file=self.get_filename(instance),
            node_name=uses_node_name(self.zntrack_type, instance),
            value_name=self.name,
            value=self.__get__(instance, self.owner),
        )

    def mkdir(self, instance):
        """Create a parent directory

        For parameters that are saved in e.g. nodes/<node_name>/file.json
        the nodes/<node_name>/ directory is created here. This is required
        for DVC to create a .gitignore file in these directories.
        """
        file = self.get_filename(instance)
        file.parent.mkdir(exist_ok=True, parents=True)

    def get_data_from_files(self, instance):
        """Load the value/s for the given instance from the file/s

        Parameters
        ----------
        instance: Node
            instance where the Descriptor is attached to.
            Similar to __get__(instance) this requires the instance
            to be passed manually.

        Returns
        -------
        any:
            returns the value loaded from file/s for the given instance.
        """
        file = self.get_filename(instance)
        file_content = utils.file_io.read_file(file)
        # The problem here is, that I can not / don't want to load all Nodes but
        # only the ones, that are in [self.node_name][self.name] for deserializing
        if uses_node_name(self.zntrack_type, instance) is not None:
            values = utils.decode_dict(
                file_content[instance.node_name].get(self.name, None)
            )
        else:
            values = utils.decode_dict(file_content.get(self.name, None))

        log.debug(f"Loading {instance.node_name} from {file}: ({values})")
        return values
