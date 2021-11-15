"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description:
"""

from .base import MetaData
from time import time
import statistics
import json
from zntrack.utils.type_hints import TypeHintParent


class TimeIt(MetaData):
    """TimeIt decorator that saves the execution time of decorated method"""

    name_of_metric = "timeit"

    def call(self, cls, *args, **kwargs):
        """Measure the execution time by storing the time
        before and after the function call
        """
        start_time = time()
        parsed_func = self.func(cls, *args, **kwargs)
        stop_time = time()

        self.save_metadata(cls, value=stop_time - start_time)

        return parsed_func


class TimeItMean(MetaData):
    """TimeIt decorator that computes the mean and std over multiple runs"""

    name_of_metric = "TimeItMean"

    def call(self, cls, *args, **kwargs):
        pass

    def __call__(self, cls: TypeHintParent, *args, **kwargs):
        """Measure the execution time by storing the time
        before and after the function call
        """
        start_time = time()
        parsed_func = self.func(cls, *args, **kwargs)
        stop_time = time()

        tmp_file_name = f"{self.name_of_metric}_{self.func_name}.json"
        tmp_file = cls.zntrack.get_temporary_file(name=tmp_file_name)

        try:
            data = json.loads(tmp_file.read_text())
        except json.decoder.JSONDecodeError:
            data = []

        data.append(stop_time - start_time)
        try:
            mean = statistics.mean(data)
            std = statistics.stdev(data)
        except statistics.StatisticsError:
            mean = data[0]
            std = 0

        tmp_file.write_text(json.dumps(data))

        self.save_metadata(
            cls, value={"mean": mean, "std": std, "runs": len(data)}, use_regex=False
        )

        return parsed_func
