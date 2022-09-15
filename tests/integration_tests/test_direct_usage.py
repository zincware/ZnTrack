"""Test using the ZnTrack Nodes without DVC"""
import random

import pandas as pd
import pytest

from zntrack import Node, dvc, exceptions, zn


class GenerateRandomNumber(Node):
    seed: int = zn.params()
    output: float = zn.outs()

    def run(self):
        random.seed(self.seed)
        self.output = random.randint(0, 100)


class MetricsAndPlots(Node):
    metrics = zn.metrics()
    plots = zn.plots()

    def run(self):
        self.metrics = {"a": 100}
        self.plots = pd.DataFrame([{"b": 1}, {"b": 2}])


class DVCOuts(Node):
    file: str = dvc.outs()

    def run(self):
        pass


def test_GenerateRandomNumber():
    rn = GenerateRandomNumber(seed=1234)

    with pytest.raises(exceptions.DataNotAvailableError):
        _ = rn.output

    assert rn.seed == 1234
    rn.run()
    assert rn.output == 99


def test_run_and_save(proj_path):
    rn = GenerateRandomNumber(seed=1234)
    rn.run_and_save()

    assert rn.seed == 1234
    assert rn.output == 99

    rn_loaded = GenerateRandomNumber.load()

    assert rn_loaded.output == 99
    assert rn_loaded.seed == 1234


def test_MetricsAndPlots():
    mp = MetricsAndPlots()
    with pytest.raises(exceptions.DataNotAvailableError):
        _ = mp.plots

    with pytest.raises(exceptions.DataNotAvailableError):
        _ = mp.metrics

    mp.run()

    assert mp.metrics == {"a": 100}
    assert pd.DataFrame([{"b": 1}, {"b": 2}]).equals(mp.plots)


def test_run_and_save_mp(proj_path):
    mp = MetricsAndPlots()
    mp.run_and_save()

    assert mp.metrics == {"a": 100}
    assert pd.DataFrame([{"b": 1}, {"b": 2}]).equals(mp.plots)

    mp_loaded = MetricsAndPlots.load()

    assert mp_loaded.metrics == {"a": 100}
    assert pd.DataFrame([{"b": 1}, {"b": 2}]).equals(mp_loaded.plots)
