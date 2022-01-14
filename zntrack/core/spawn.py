from __future__ import annotations

import abc
import itertools
import logging
import pathlib

from zntrack.core.base import Node
from zntrack.utils.constants import zn_types

log = logging.getLogger(__name__)


class SpawnNode(Node, abc.ABC):
    is_spawned: bool = False

    _iterator = None

    def iterator(self):
        params_lst = []
        params_names = []
        for p_name, p_val in self._descriptor_list.filter(
            zntrack_type=zn_types.iterable
        ).items():
            params_lst.append(p_val)
            params_names.append(p_name)

        for combination in itertools.product(*params_lst):
            parameter_dict = {x[0]: x[1] for x in zip(params_names, combination)}
            # check if the current combination fits the filter
            if not self.spawn_filter(**parameter_dict):
                log.debug(f"Skipping Node with params: {parameter_dict}")
                continue

            # Create an instance
            instance = self.load(name=self.node_name)
            instance.is_spawned = True
            # update the iterable types with type params
            for value, name in zip(combination, params_names):
                setattr(instance, name, value)
            log.debug(f"Spawning Node with params: {parameter_dict}")
            # need to load after the params are set, so that the hash is correct
            instance._load()
            yield instance

    def spawn_filter(self, **kwargs) -> bool:
        """Check if a Node with the given parameters should be spawned

        Parameters
        ----------
        kwargs: dict
            a dictionary with zn.iterable attribute names as keys and the respective
            values of this iteration.

        Examples
        --------
        >>> from zntrack import zn
        >>> class Spawner(SpawnNode)
        >>>     iterable = zn.Iterable([1, 2, 3])
        >>>     def spawn_filter(self, iterable):
        >>>         # do not spawn nodes for iterable >= 2
        >>>         return iterable < 2
        >>>     def run(self):
        >>>         pass # do some computation here with self.iterable
        Returns
        -------
        bool:
            spawn the node
        """
        return True

    def __iter__(self):
        self._iterator = self.iterator()
        return self

    def __next__(self) -> SpawnNode:
        return next(self._iterator)

    def save(self):
        super(SpawnNode, self).save()
        # need to overwrite the iterable params
        self._save_to_file(
            file=pathlib.Path("params.yaml"),
            zntrack_type=[zn_types.params, zn_types.iterable],
            key=self.node_name,
        )

    @property
    def node_name(self) -> str:
        node_name = super(SpawnNode, self).node_name
        if self.is_spawned:
            return f"{node_name}_{self._descriptor_list.hash}"
        else:
            return node_name

    @node_name.setter
    def node_name(self, value):
        """Overwrite the default node name based on the class name"""
        self._node_name = value

    def write_graph(
        self,
        silent: bool = False,
        nb_name: str = None,
        no_commit: bool = False,
        external: bool = False,
        always_changed: bool = False,
        no_exec: bool = True,
        force: bool = True,
        no_run_cache: bool = False,
    ):
        self.save()
        for node in self:
            Node.write_graph(
                node,
                silent,
                nb_name,
                no_commit,
                external,
                always_changed,
                no_exec,
                force,
                no_run_cache,
            )
