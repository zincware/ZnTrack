import abc

from zntrack.core.base import Node


class SpawnNode(Node, abc.ABC):
    def iterator(self):
        # TODO must set all params
        # TODO must change the ZnTrackOption to iterable = False
        for param in self.zntrack.option_tracker.zn_iterables:
            for value in getattr(self, param.name):
                param.iterable = False
                instance = self.load()
                setattr(instance, param.name, value)
                yield instance

    def __iter__(self):
        self.__dict__["iterator"] = self.iterator()
        return self

    def __next__(self):
        return next(self.__dict__["iterator"])
