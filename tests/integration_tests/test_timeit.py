import time

import pytest

from zntrack import Node, zn
from zntrack.metadata import TimeIt
from zntrack.utils.exceptions import DescriptorMissing


class SleepClassNoMetadata(Node):
    sleep_for = zn.params(1)

    @TimeIt
    def run(self):
        time.sleep(self.sleep_for)


class SleepClass(Node):
    sleep_for = zn.params(1)
    timeit_metrics = zn.metadata()

    @TimeIt
    def run(self):
        time.sleep(self.sleep_for)


class SleepClassLoop(Node):
    sleep_for = zn.params(0.1)
    timeit_metrics = zn.metadata()
    iterations = zn.params(30)

    def run(self):
        for _ in range(30):
            self.sleep()

    @TimeIt
    def sleep(self):
        time.sleep(self.sleep_for)


def test_timeit_no_metadata_err(proj_path):
    with pytest.raises(DescriptorMissing):
        SleepClassNoMetadata().run_and_save()


def test_timeit(proj_path):
    SleepClass().run_and_save()
    assert pytest.approx(SleepClass.load().timeit_metrics["run:timeit"], 0.1) == 1.0


def test_timeit_loop(proj_path):
    sleep_class = SleepClassLoop()
    sleep_class.run_and_save()
    assert (
        pytest.approx(SleepClassLoop.load().timeit_metrics["sleep:timeit"]["mean"], 0.01)
        == 0.1
    )
    assert SleepClassLoop.load().timeit_metrics["sleep:timeit"]["std"] < 1e-3
    assert len(SleepClassLoop.load().timeit_metrics["sleep:timeit"]["values"]) == 30
