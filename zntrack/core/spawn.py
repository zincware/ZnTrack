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

    def iterator(self):
        # TODO must set all params
        # TODO must change the ZnTrackOption to iterable = False
        params_lst = []
        params_names = []
        for p_name, p_val in self._descriptor_list.filter(
            zntrack_type=zn_types.iterable
        ).items():
            params_lst.append(p_val)
            params_names.append(p_name)

        for combination in itertools.product(*params_lst):
            instance = self.load()
            # update the iterable types with type params
            for value, name in zip(combination, params_names):
                setattr(instance, name, value)
            log.debug(
                "Spawning Node with params:"
                f" { {x[0]: x[1] for x in zip(combination, params_names)} }"
            )
            instance.is_spawned = True
            yield instance

    def __iter__(self):
        self.__dict__["_iterator"] = self.iterator()
        return self

    def __next__(self) -> SpawnNode:
        return next(self.__dict__["_iterator"])

    def save(self):
        super(SpawnNode, self).save()
        if self.is_spawned:
            self._save_to_file(
                file=pathlib.Path("params.yaml"),
                zntrack_type=[zn_types.params, zn_types.iterable],
                key=self.node_name,
            )

    @property
    def node_name(self) -> str:
        node_name = super(SpawnNode, self).node_name
        return f"{node_name}_{self._descriptor_list.hash}"

    @node_name.setter
    def node_name(self, value):
        """Overwrite the default node name based on the class name"""
        self._node_name = value

    # def write_graph(
    #     self,
    #     silent: bool = False,
    #     nb_name: str = None,
    #     no_commit: bool = False,
    #     external: bool = False,
    #     always_changed: bool = False,
    #     no_exec: bool = True,
    #     force: bool = True,
    #     no_run_cache: bool = False,
    # ):
    #     for node in self:
    #         Node.write_graph(
    #             node,
    #             silent,
    #             nb_name,
    #             no_commit,
    #             external,
    #             always_changed,
    #             no_exec,
    #             force,
    #             no_run_cache,
    #         )

    def spawn_nodes(self):
        for node in self:
            node.write_graph()
