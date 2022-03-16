from time import time

from .base import MetaData


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

        self.save_metadata(cls, value=stop_time - start_time)

        return parsed_func
