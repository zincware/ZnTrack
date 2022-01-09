from __future__ import annotations

import abc
import itertools

from zntrack.core.base import Node
from zntrack.utils.utils import dict_hash


class SpawnNode(Node, abc.ABC):
    def iterator(self):
        # TODO must set all params
        # TODO must change the ZnTrackOption to iterable = False
        params_lst = []
        params_names = []
        for param in self.zntrack.option_tracker.zn_iterables:
            params_lst.append(getattr(self, param.name))
            params_names.append(param.name)

        for combination in itertools.product(*params_lst):
            instance = self.load()
            instance.zntrack.option_tracker.check_iterable = False
            for value, name in zip(combination, params_names):
                setattr(instance, name, value)
            yield instance

    def __iter__(self):
        self.__dict__["iterator"] = self.iterator()
        return self

    def __next__(self) -> SpawnNode:
        return next(self.__dict__["iterator"])

    @property
    def node_name(self) -> str:
        return f"node_{dict_hash(self.zntrack.option_tracker.get_dict(self))}"

    def write_dvc(self):
        [x.write_dvc() for x in self]
