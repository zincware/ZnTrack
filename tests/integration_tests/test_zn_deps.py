import json
import pathlib
import subprocess

import pytest

from zntrack import zn
from zntrack.core.base import Node
from zntrack.utils.utils import run_dvc_cmd


class FirstNode(Node):
    outs = zn.outs()

    def run(self):
        self.outs = 42


class LastNode(Node):
    first_node: FirstNode = zn.deps(FirstNode.load())
    outs = zn.outs()

    def run(self):
        self.outs = self.first_node.outs / 2


class LastNodeNoLoad(Node):
    first_node: FirstNode = zn.deps(FirstNode)
    outs = zn.outs()

    def run(self):
        self.outs = self.first_node.outs / 2


class LastNodeNoDefault(Node):
    first_node: FirstNode = zn.deps()
    outs = zn.outs()

    def __init__(self, first_node=None, **kwargs):
        super(LastNodeNoDefault, self).__init__(**kwargs)
        self.first_node = first_node

    def run(self):
        self.outs = self.first_node.outs / 2


def test_LastNodeNoLoad(proj_path):
    FirstNode().write_graph(run=True)
    LastNodeNoLoad().write_graph(run=True)

    assert LastNodeNoLoad.load().outs == 21


@pytest.mark.parametrize(
    ("load_node", "run"), ((False, False), (True, True), (True, False), (False, True))
)
def test_LastNodeNoDefault(proj_path, load_node, run):
    FirstNode().write_graph(run=run)
    first_node = FirstNode.load() if load_node else FirstNode
    LastNodeNoDefault(first_node=first_node).write_graph(run=run)
    if not run:
        run_dvc_cmd(["repro"])

    assert LastNodeNoDefault.load().outs == 21


def test_base_run(proj_path):
    FirstNode().write_graph(run=True)
    LastNode().write_graph(run=True)

    assert LastNode.load().outs == 21


@pytest.fixture()
def zntrack_dict() -> dict:
    return {
        "LastNode": {
            "first_node": {
                "_type": "ZnTrackType",
                "value": {
                    "cls": "FirstNode",
                    "module": "test_zn_deps",
                    "name": "FirstNode",
                },
            }
        }
    }


def test_assert_write_file(proj_path, zntrack_dict):
    FirstNode().write_graph()
    LastNode().write_graph()

    zntrack_dict_loaded = json.loads(pathlib.Path("zntrack.json").read_text())

    assert zntrack_dict_loaded == zntrack_dict


def test_assert_read_file(proj_path, zntrack_dict):
    pathlib.Path("zntrack.json").write_text(json.dumps(zntrack_dict))

    assert isinstance(LastNode.load().first_node, FirstNode)


class FirstNodeParams(Node):
    number: int = zn.params()


class SecondNodeParams(Node):
    first_node_params: FirstNodeParams = zn.deps(FirstNodeParams)

    negative_number: int = zn.params()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.negative_number = -1 * self.first_node_params.number


@pytest.mark.parametrize("number", (5, -5))
def test_ParamsFromNodeNoLoad(proj_path, number):
    FirstNodeParams(number=number).write_graph()
    SecondNodeParams().write_graph()

    assert FirstNodeParams.load().number == number
    assert SecondNodeParams.load().negative_number == -1 * number
