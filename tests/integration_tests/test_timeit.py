import os
import shutil
import subprocess
import time

import pytest

from zntrack import Node, zn
from zntrack.metadata import TimeIt
from zntrack.metadata.base import DescriptorMissing


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


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


def test_timeit_no_metadata_err(proj_path):
    with pytest.raises(DescriptorMissing):
        SleepClassNoMetadata().run_and_save()


def test_timeit(proj_path):
    SleepClass().run_and_save()
    assert SleepClass.load().timeit_metrics["run:timeit"] - 1.0 < 0.1
