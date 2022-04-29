import dataclasses
import statistics
from time import time

from zntrack.metadata.base import MetaData


@dataclasses.dataclass
class AggregateData:
    values: list = dataclasses.field(default_factory=list)
    mean: float = None
    std: float = None

    def update(self):
        try:
            self.mean = statistics.mean(self.values)
            self.std = statistics.stdev(self.values)
        except statistics.StatisticsError:
            pass


class TimeIt(MetaData):
    """TimeIt decorator that saves the execution time of decorated method"""

    name_of_metric = "timeit"

    def __call__(self, cls, *args, **kwargs):
        """Measure the execution time by storing the time
        before and after the function call
        """
        start_time = time()
        parsed_func = self.func(cls, *args, **kwargs)
        stop_time = time()

        value = stop_time - start_time

        metadata, _ = self.get_history(cls)
        history = metadata.get(self.name, AggregateData())
        if isinstance(history, dict):
            history = AggregateData(**history)
        history.values.append(value)
        history.update()
        history = dataclasses.asdict(history)

        self.save_metadata(cls, value=history)

        return parsed_func
