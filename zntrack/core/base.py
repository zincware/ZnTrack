"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""
from __future__ import annotations

import json
import logging
import pathlib
import sys

import znjson

import zntrack
from zntrack.core.dvcgraph import GraphWriter
from zntrack.utils.utils import deprecated

log = logging.getLogger(__name__)


class Node(GraphWriter):
    """Main parent class for all ZnTrack Node"""

    is_loaded: bool = False

    _module = None

    @property
    def module(self) -> str:
        """Module from which to import <name>

        Used for from <module> import <name>

        Notes
        -----
        this can be changed when using nb_mode
        """
        if self._module is None:
            if self.__class__.__module__ == "__main__":
                if pathlib.Path(sys.argv[0]).stem == "ipykernel_launcher":
                    # special case for e.g. testing
                    return self.__class__.__module__
                return pathlib.Path(sys.argv[0]).stem
            else:
                return self.__class__.__module__
        return self._module

    @deprecated(
        reason="Please see <migration tutorial> from v0.2 to v0.3 in the documentation",
        version="v0.3",
    )
    def __call__(self, *args, **kwargs):
        """Still here for a depreciation warning for migrating to class based ZnTrack"""
        pass

    def save(self):
        """Save Class state to files"""
        # Save dvc.<option>, dvc.deps, zn.Method
        self._save_to_file(
            file=pathlib.Path("zntrack.json"),
            zntrack_type=["dvc", "deps", "method"],
            key=self.node_name,
        )
        # Save dvc/zn.<params>
        self._save_to_file(
            file=pathlib.Path("params.yaml"), zntrack_type="params", key=self.node_name
        )
        # Save zn.<option> including zn.outs, zn.metrics, ...
        for option, values in self._descriptor_list.filter(
            zntrack_type=["zn", "metadata"], return_with_type=True
        ).items():
            file = pathlib.Path("nodes") / self.node_name / f"{option}.json"
            log.debug(f"Saving {option} to {file}")
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(json.dumps(values, indent=4, cls=znjson.ZnEncoder))

    def _load(self):
        """Load class state from files"""
        self._load_from_file(
            file=pathlib.Path("params.yaml"), key=self.node_name, raise_key_error=False
        )
        self._load_from_file(
            file=pathlib.Path("zntrack.json"), key=self.node_name, raise_key_error=False
        )
        for option in self._descriptor_list.filter(
            zntrack_type=["zn", "metadata"], return_with_type=True
        ):
            self._load_from_file(
                file=pathlib.Path("nodes") / self.node_name / f"{option}.json",
                raise_key_error=False,
            )
        self.is_loaded = True

    @classmethod
    def load(cls, name=None) -> Node:
        """

        Parameters
        ----------
        name: Node name

        Returns
        -------
        Instance of this class with the state loaded from files

        Examples
        --------
        Always have this, so that the name can be passed through

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        """

        try:
            instance = cls(name=name)
        except TypeError:
            log.warning(
                "Can not pass <name> to the super.__init__ and trying workaround! This"
                " can lead to unexpected behaviour and can be avoided by passing (*args,"
                " **kwargs) to the super().__init__(*args, **kwargs)"
            )
            instance = cls()
            if name not in (None, cls.__name__):
                instance.node_name = name

        instance._load()

        if zntrack.config.nb_name is not None:
            # TODO maybe check if it exists and otherwise keep default?
            instance._module = f"{zntrack.config.nb_class_path}.{cls.__name__}"

        return instance

    def run_and_save(self):
        """Main method to run for the actual calculation"""
        self.run()
        self.save()

    # @abc.abstractmethod
    def run(self):
        """Overwrite this method for the actual calculation"""
        raise NotImplementedError
