"""ZnTrack metadata decorator."""
import contextlib
import dataclasses
import statistics
from time import time

from zntrack.metadata.base import MetaData


@dataclasses.dataclass
class AggregateData:
    """Dataclass to collect the values together with their mean and std."""

    values: list = dataclasses.field(default_factory=list)
    mean: float = None
    std: float = None

    def update(self):
        """Recompute mean and standard deviation."""
        with contextlib.suppress(statistics.StatisticsError):
            self.mean = statistics.mean(self.values)
            self.std = statistics.stdev(self.values)


class TimeIt(MetaData):
    """TimeIt decorator that saves the execution time of decorated method."""

    name_of_metric = "timeit"

    def __call__(self, cls, *args, **kwargs):
        """Measure the execution time by storing the time."""
        start_time = time()
        parsed_func = self.func(cls, *args, **kwargs)
        stop_time = time()

        value = stop_time - start_time

        metadata, _ = self.get_history(cls)
        history = metadata.get(self.name, AggregateData())
        if isinstance(history, dict):
            history = AggregateData(**history)
        elif isinstance(history, float):
            history = AggregateData(values=[history])
        # add new value and update mean / std
        history.values.append(value)
        history.update()
        # convert back to either float for single value or dict for multiple values.
        if len(history.values) > 1:
            history = dataclasses.asdict(history)
        else:
            history = history.values[0]

        self.save_metadata(cls, value=history)

        return parsed_func
