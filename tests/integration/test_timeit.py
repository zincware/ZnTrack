import time

import pytest

import zntrack


class SleepClassNoMetadata(zntrack.Node):
    sleep_for = zntrack.zn.params(1)

    @zntrack.tools.timeit("metadata")
    def run(self):
        time.sleep(self.sleep_for)


class SleepClass(zntrack.Node):
    sleep_for = zntrack.zn.params(1)
    timeit_metrics = zntrack.zn.metrics()

    @zntrack.tools.timeit("timeit_metrics")
    def run(self):
        time.sleep(self.sleep_for)


class SleepClassLoop(zntrack.Node):
    sleep_for = zntrack.zn.params(0.1)
    timeit_metrics = zntrack.zn.metrics()
    iterations = zntrack.zn.params(30)

    def run(self):
        for _ in range(30):
            self.sleep()

    @zntrack.tools.timeit("timeit_metrics")
    def sleep(self):
        time.sleep(self.sleep_for)


def test_timeit_no_metadata_err(proj_path):
    with pytest.raises(AttributeError):
        SleepClassNoMetadata().run()


@pytest.mark.parametrize("eager", [True, False])
def test_timeit(proj_path, eager):
    with zntrack.Project() as project:
        sleep_class = SleepClass()

    project.run(eager=eager)
    if not eager:
        sleep_class.load()
    assert pytest.approx(sleep_class.timeit_metrics["run"], 0.1) == 1.0


@pytest.mark.parametrize("eager", [True, False])
def test_timeit_loop(proj_path, eager):
    with zntrack.Project() as project:
        sleep_class = SleepClassLoop()
    project.run(eager=eager)
    if not eager:
        sleep_class.load()

    assert pytest.approx(sleep_class.timeit_metrics["sleep"]["mean"], 0.1) == 0.1
    assert sleep_class.timeit_metrics["sleep"]["std"] < 1e-2
    assert len(sleep_class.timeit_metrics["sleep"]["values"]) == 30
